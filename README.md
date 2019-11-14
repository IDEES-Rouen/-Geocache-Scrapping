# geoscrap

0 - Modify script with your ident/password from geocache

- In line 54 of `GeocachingExtractorSpider.py`
- In line 46 of `GeocachingSpider.py`
- crontab if you want another

1 - Build docker image

```shell script
export UID=$(id -u)
export GID=$(id -g)
docker-compose build --build-arg UID="$(id -u)" --build-arg GID="$(id -g)"
```

2 - Run Docker container based on step 1

```shell script
sudo docker-compose up -d geocache_scrap
```

3 - dump data collected by 2
```shell script
docker run --rm -v geoscrap_geo_scrapy_volume:/backup ubuntu tar czCv /backup . > geocache.tar.gz
```
