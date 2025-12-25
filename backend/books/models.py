from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

class Book(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="books")
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    pub_date = models.DateField(null=True, blank=True)
    isbn13 = models.CharField(max_length=30, blank=True)
    cover = models.URLField(blank=True)
    description = models.TextField(blank=True)
    customer_review_rank = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)