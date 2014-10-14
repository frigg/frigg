from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^webhooks/github/$', 'frigg.builds.api.github_webhook'),
    url(r'^admin/', include(admin.site.urls)),

    url(
        r'^auth/logout/$',
        'django.contrib.auth.views.logout',
        {'next_page': 'https://frigg.io'},
        name='logout'
    ),
    url(r'^auth/', include('social_auth.urls')),
    url(r'^', include('frigg.builds.urls')),
)
