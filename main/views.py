from django.shortcuts import render
from django.db.models import Q, F
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import ActiveScanner, Keyword, Listing, Location, ScannerLocationMapping
from .serializers import ActiveScannerSerializer, KeywordSerializer, ListingSerializer, LocationSerializer, ScannerLocationMappingSerializer
from rest_framework.pagination import PageNumberPagination

# Create your views here.

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [AllowAny]  # Change this to IsAuthenticated in production

class ActiveScannerViewSet(viewsets.ModelViewSet):
    queryset = ActiveScanner.objects.all()
    serializer_class = ActiveScannerSerializer
    permission_classes = [AllowAny]  # Change this to IsAuthenticated in production
    
    def create(self, request, *args, **kwargs):
        # Extract location_ids from request data
        location_ids = request.data.pop('location_ids', [])
        
        # Create the scanner
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scanner = serializer.save()
        
        # Create location mappings
        for location_id in location_ids:
            try:
                location = Location.objects.get(id=location_id)
                ScannerLocationMapping.objects.create(
                    scanner=scanner,
                    location=location,
                    is_active=True
                )
            except Location.DoesNotExist:
                pass
        
        # Return the created scanner with location data
        return Response(
            ActiveScannerSerializer(scanner).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        # Extract location_ids from request data
        location_ids = request.data.pop('location_ids', None)
        
        # Update the scanner
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Update location mappings if provided
        if location_ids is not None:
            # Deactivate all existing mappings
            ScannerLocationMapping.objects.filter(scanner=instance).update(is_active=False)
            
            # Create or activate mappings for the provided location_ids
            for location_id in location_ids:
                try:
                    location = Location.objects.get(id=location_id)
                    mapping, created = ScannerLocationMapping.objects.get_or_create(
                        scanner=instance,
                        location=location,
                        defaults={'is_active': True}
                    )
                    if not created:
                        mapping.is_active = True
                        mapping.save()
                except Location.DoesNotExist:
                    pass
        
        # Return the updated scanner with location data
        return Response(ActiveScannerSerializer(instance).data)

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
        search_location = self.request.query_params.get('search_location', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        max_distance = self.request.query_params.get('max_distance', None)
        watchlist = self.request.query_params.get('watchlist', None)
        
        if query:
            queryset = queryset.filter(query=query)
            
        if category:
            queryset = queryset.filter(search_title=category)
            
        # Filter by search location (where the search originated from)
        if search_location:
            queryset = queryset.filter(search_location=search_location)
        
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
        # Get unique queries from listings
        queries = list(Listing.objects.values_list('query', flat=True).distinct())
        
        # Get unique categories from listings
        categories = list(Listing.objects.values_list('search_title', flat=True).distinct())
        
        # Get the search locations from listings
        search_locations = list(Listing.objects.values_list('search_location', flat=True).distinct())
        
        # Filter out None and empty values and ensure unique values
        queries = sorted(list(set(q for q in queries if q)))
        categories = sorted(list(set(c for c in categories if c)))
        search_locations = sorted(list(set(loc for loc in search_locations if loc)))
        
        return Response({
            'queries': queries,
            'categories': categories,
            'search_locations': search_locations  # Use search_locations instead of scanner_locations
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

class ScannerLocationMappingViewSet(viewsets.ModelViewSet):
    queryset = ScannerLocationMapping.objects.all()
    serializer_class = ScannerLocationMappingSerializer
    permission_classes = [AllowAny]  # Change to IsAuthenticated in production
    
    @action(detail=False, methods=['get'])
    def by_scanner(self, request):
        scanner_id = request.query_params.get('scanner_id')
        if not scanner_id:
            return Response({"error": "Scanner ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        mappings = ScannerLocationMapping.objects.filter(scanner_id=scanner_id)
        serializer = self.get_serializer(mappings, many=True)
        return Response(serializer.data)
