from django.contrib import admin
from .models import User, Movie, Comic, Blog, Like, Comment, Profile

admin.site.register(User)
admin.site.register(Movie)
admin.site.register(Comic)
admin.site.register(Blog)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Profile)
