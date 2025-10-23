# 1. tail the failed container
docker logs bioprocess-analytics-microservice-auth-1 --tail 50

# 2. if it’s very short, also look at the others
for svc in auth user batch; do
  echo "========== $svc =========="
  docker logs bioprocess-analytics-microservice-${svc}-1 --tail 20
done
