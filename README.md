# geoscrap

1 - Build docker image

```shell script
export UID=$(id -u)
export GID=$(id -g)
docker-compose build --build-arg UID="$(id -u)" --build-arg GID="$(id -g)"
```

2 - Run Docker container based on step 1

```shell script
docker-compose up -d geocache_scrapy
```

3 - dump data collected by 2
```shell script

```
