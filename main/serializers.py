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
    locations_data = ScannerLocationMappingSerializer(source='scannerlocationmapping_set', many=True, read_only=True)
    location_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ActiveScanner
        fields = ['id', 'category', 'query', 'town', 'status', 'locations_data', 'location_ids']
    
    def create(self, validated_data):
        location_ids = validated_data.pop('location_ids', [])
        scanner = ActiveScanner.objects.create(**validated_data)
        
        # Create mappings for each location
        for location_id in location_ids:
            try:
                location = Location.objects.get(id=location_id)
                ScannerLocationMapping.objects.create(scanner=scanner, location=location)
                
                # Set town to first location name for backward compatibility if not provided
                if not scanner.town and location == Location.objects.filter(id__in=location_ids).first():
                    scanner.town = location.name
                    scanner.save()
            except Location.DoesNotExist:
                pass
        
        return scanner
    
    def update(self, instance, validated_data):
        location_ids = validated_data.pop('location_ids', None)
        
        # Update scanner fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update location mappings if provided
        if location_ids is not None:
            # Remove existing mappings
            instance.scannerlocationmapping_set.all().delete()
            
            # Create new mappings
            for location_id in location_ids:
                try:
                    location = Location.objects.get(id=location_id)
                    ScannerLocationMapping.objects.create(scanner=instance, location=location)
                    
                    # Update town to first location name for backward compatibility
                    if location == Location.objects.filter(id__in=location_ids).first():
                        instance.town = location.name
                        instance.save()
                except Location.DoesNotExist:
                    pass
        
        return instance

class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__' 