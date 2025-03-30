from rest_framework import serializers
from .models import ActiveScanner, Keyword, Listing, Location, ScannerLocationMapping

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'marketplace_url_slug']

class ScannerLocationMappingSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    location_slug = serializers.CharField(source='location.marketplace_url_slug', read_only=True)
    
    class Meta:
        model = ScannerLocationMapping
        fields = ['id', 'location', 'location_name', 'location_slug', 'is_active']

class ActiveScannerSerializer(serializers.ModelSerializer):
    locations_data = serializers.SerializerMethodField()
    
    class Meta:
        model = ActiveScanner
        fields = ['id', 'category', 'query', 'status', 'locations_data']
        
    def get_locations_data(self, obj):
        # Get all location mappings for this scanner
        mappings = ScannerLocationMapping.objects.filter(scanner=obj, is_active=True)
        
        # Format the location data
        return [
            {
                'mapping_id': mapping.id,
                'location': mapping.location.id,
                'location_name': mapping.location.name,
                'marketplace_slug': mapping.location.marketplace_url_slug,
                'is_active': mapping.is_active
            }
            for mapping in mappings
        ]

class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__' 