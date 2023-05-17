while read line; do
  git reset --hard $line
  echo "commit:$line" >> /go/src/github.com/docker/docker/trans/buildcache.log
  docker build --build-arg HTTP_PROXY=http://192.168.162.239:7890 \
	 --build-arg HTTPS_PROXY=http://192.168.162.239:7890 \
	 -f Dockerfile -t grafana:$line ./
done < commits.txt

