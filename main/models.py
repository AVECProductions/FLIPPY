from django.db import models

class ActiveScanner(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.CharField(max_length=100)
    query = models.CharField(max_length=255)
    town = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='stopped')

    class Meta:
        db_table = 'active_scanners'
        verbose_name = 'Active Scanner'
        verbose_name_plural = 'Active Scanners'

    def __str__(self):
        return f"{self.query} in {self.town}"


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
    location = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)
    distance = models.IntegerField(null=True)
    url = models.TextField(null=True)
    img = models.TextField(null=True)
    query = models.CharField(max_length=50, null=True)
    search_title = models.TextField(null=True)
    watchlist = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'listings'
        verbose_name = 'Listing'
        verbose_name_plural = 'Listings'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.price}"