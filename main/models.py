from django.db import models

class Location(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    marketplace_url_slug = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'locations'
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
    
    def __str__(self):
        return self.name

class ActiveScanner(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100)
    query = models.CharField(max_length=255)
    locations = models.ManyToManyField(Location, through='ScannerLocationMapping', related_name='scanners')
    status = models.CharField(max_length=20, default='stopped')

    class Meta:
        db_table = 'active_scanners'
        verbose_name = 'Active Scanner'
        verbose_name_plural = 'Active Scanners'

    def __str__(self):
        # Get the first location name if available
        location_name = self.locations.first().name if self.locations.exists() else 'multiple locations'
        return f"{self.query} in {location_name}"

class ScannerLocationMapping(models.Model):
    id = models.AutoField(primary_key=True)
    scanner = models.ForeignKey(ActiveScanner, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'scanner_location_mappings'
        unique_together = ('scanner', 'location')
        verbose_name = 'Scanner Location Mapping'
        verbose_name_plural = 'Scanner Location Mappings'
    
    def __str__(self):
        return f"{self.scanner.query} in {self.location.name}"

class Keyword(models.Model):
    id = models.AutoField(primary_key=True)
    keyword = models.CharField(max_length=50, null=True)
    filterID = models.IntegerField()

    class Meta:
        db_table = 'keywords'
        verbose_name = 'Keyword'
        verbose_name_plural = 'Keywords'

    def __str__(self):
        return self.keyword


class Listing(models.Model):
    listing_idx = models.AutoField(primary_key=True)
    price = models.CharField(max_length=50, null=True)
    title = models.TextField(null=True)
    location = models.CharField(max_length=50, null=True)  # This is the listing's location (e.g., "Denver, CO")
    description = models.TextField(null=True)
    distance = models.IntegerField(null=True)
    url = models.TextField(null=True)
    img = models.TextField(null=True)
    query = models.CharField(max_length=50, null=True)
    search_title = models.TextField(null=True)
    # Add new fields for scanner and search location
    scanner_id = models.IntegerField(null=True)  # ID of the scanner that found this listing
    search_location = models.CharField(max_length=100, null=True)  # Location where the search was performed
    watchlist = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'listings'
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.price}"