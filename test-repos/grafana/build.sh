i=0
while read line; do
  git reset --hard $line
  echo "commit:$line" >> /go/src/github.com/docker/docker/trans/buildcache.log
  echo "commit:$line" >> /go/src/github.com/docker/docker/trans/buildtime.log
  docker build --build-arg HTTP_PROXY=http://202.114.7.81:7890 \
	  --build-arg HTTPS_PROXY=http://202.114.7.81:7890 \
	  -f Dockerfile -t grafana:$line ./
  if [ $? -eq 0 ]
  then
	  i=$((i+1))
  else
	  echo "failed" >> /go/src/github.com/docker/docker/trans/buildcache.log
	  echo "failed" >> /go/src/github.com/docker/docker/trans/buildtime.log
  fi
  if [ $i -eq 20 ]
  then
          break
  else
          continue
  fi
done < commits.txt
