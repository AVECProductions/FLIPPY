from rest_framework import serializers
from .models import ActiveScanner, Keyword, Listing

class ActiveScannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveScanner
        fields = '__all__'

class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__' 