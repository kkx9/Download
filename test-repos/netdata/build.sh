while read line; do
  git reset --hard $line
  echo "commit:$line" >> /go/src/github.com/docker/docker/trans/buildcache.log
  echo "commit:$line" >> /go/src/github.com/docker/docker/trans/buildtime.log
  docker build --build-arg HTTP_PROXY=http://202.114.7.81:7890 \
          --build-arg HTTPS_PROXY=http://202.114.7.81:7890 \
          -f packaging/docker/Dockerfile -t netdata:$line ./
done < commits20.txt
