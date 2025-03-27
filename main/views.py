from django.shortcuts import render
from django.db.models import Q, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ActiveScanner, Keyword, Listing
from .serializers import ActiveScannerSerializer, KeywordSerializer, ListingSerializer
from rest_framework.pagination import PageNumberPagination

# Create your views here.

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

class ActiveScannerViewSet(viewsets.ModelViewSet):
    queryset = ActiveScanner.objects.all()
    serializer_class = ActiveScannerSerializer
    # Allow any access for development
    permission_classes = [AllowAny]  # Change this to IsAuthenticated in production
    
    @action(detail=False, methods=['get'])
    def locations(self, request):
        """Return unique town values from active scanners"""
        locations = ActiveScanner.objects.values_list('town', flat=True).distinct()
        return Response(list(locations))

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all().order_by('-created_at')
    serializer_class = ListingSerializer
    permission_classes = [AllowAny]  # Change this to IsAuthenticated in production
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = Listing.objects.all().order_by('-created_at')
        
        # Apply filters based on query parameters
        query = self.request.query_params.get('query', None)
        category = self.request.query_params.get('category', None)
        scanner_location = self.request.query_params.get('scanner_location', None)  # Renamed from 'location'
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        max_distance = self.request.query_params.get('max_distance', None)
        watchlist = self.request.query_params.get('watchlist', None)
        
        if query:
            queryset = queryset.filter(query=query)
            
        if category:
            queryset = queryset.filter(search_title=category)
            
        # Filter by scanner location (where the search originated from)
        if scanner_location:
            # Get all scanner IDs that match this location
            scanner_ids = ActiveScanner.objects.filter(town=scanner_location).values_list('id', flat=True)
            # Filter listings by matching query field to these scanner queries
            scanner_queries = ActiveScanner.objects.filter(id__in=scanner_ids).values_list('query', flat=True)
            queryset = queryset.filter(query__in=scanner_queries)
        
        # Apply distance filter if provided
        if max_distance and max_distance.isdigit():
            queryset = queryset.filter(distance__lte=int(max_distance))
        
        # Simplified price filtering without REGEXP_REPLACE
        if min_price:
            # Filter listings with numeric prices that are >= min_price
            # This is a simpler approach that will work with SQL Server
            # It may not catch all valid prices but should work for most cases
            try:
                min_price_value = float(min_price)
                # First filter out listings with no price or non-numeric prices
                queryset = queryset.filter(
                    price__regex=r'[$]?[0-9]+'
                )
                # Then do a string comparison which works for basic "$123" format
                queryset = queryset.filter(
                    Q(price__regex=fr'[$]?[0-9][0-9][0-9]+') |  # $100 or more
                    Q(price__regex=fr'[$]?[0-9][0-9]') & Q(price__regex=fr'[^0-9][{min_price_value}][^0-9]') |  # $XX where XX >= min
                    Q(price__regex=fr'[$]?[0-9]') & Q(price__gte=fr'${min_price_value}')  # Single digit that's >= min
                )
            except (ValueError, TypeError):
                # If min_price is not a valid number, ignore this filter
                pass
            
        if max_price:
            # Similar approach for max_price
            try:
                max_price_value = float(max_price)
                # First filter for listings with prices
                queryset = queryset.filter(
                    price__regex=r'[$]?[0-9]+'
                )
                # Basic string comparison - will work for most common price formats
                queryset = queryset.exclude(
                    price__regex=fr'[$][0-9][0-9][0-9][0-9]+')  # Exclude prices with 4+ digits after $
                queryset = queryset.exclude(
                    price__regex=fr'[$][{max_price_value+1}-9][0-9][0-9]')  # Exclude $X00 where X > max_price_value/100
            except (ValueError, TypeError):
                # If max_price is not a valid number, ignore this filter
                pass
            
        if watchlist and watchlist.lower() == 'true':
            queryset = queryset.filter(watchlist=True)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """Return available filter options"""
        # Use distinct() to avoid duplicates
        queries = list(Listing.objects.values_list('query', flat=True).distinct())
        categories = list(Listing.objects.values_list('search_title', flat=True).distinct())
        
        # Get the scanner locations (towns) that have listings
        scanner_locations = list(ActiveScanner.objects.values_list('town', flat=True).distinct())
        
        # Filter out None and empty values and ensure unique values
        queries = sorted(list(set(q for q in queries if q)))
        categories = sorted(list(set(c for c in categories if c)))
        scanner_locations = sorted(list(set(loc for loc in scanner_locations if loc)))
        
        return Response({
            'queries': queries,
            'categories': categories,
            'scanner_locations': scanner_locations
        })

class KeywordViewSet(viewsets.ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    permission_classes = [AllowAny]  # Change this to IsAuthenticated in production
    
    @action(detail=False, methods=['get'], url_path='by-scanner')
    def by_scanner(self, request):
        scanner_id = request.query_params.get('scannerId')
        if not scanner_id:
            return Response({"error": "Scanner ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        keywords = Keyword.objects.filter(filterID=scanner_id)
        serializer = self.get_serializer(keywords, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        scanner_id = request.data.get('scannerId')
        keywords = request.data.get('keywords', [])
        
        if not scanner_id:
            return Response({"error": "Scanner ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Delete existing keywords for this scanner
        Keyword.objects.filter(filterID=scanner_id).delete()
        
        # Create new keywords
        for keyword_text in keywords:
            if keyword_text.strip():  # Only create non-empty keywords
                Keyword.objects.create(
                    keyword=keyword_text.strip(),
                    filterID=scanner_id
                )
        
        # Return the updated list
        updated_keywords = Keyword.objects.filter(filterID=scanner_id)
        serializer = self.get_serializer(updated_keywords, many=True)
        return Response(serializer.data)
