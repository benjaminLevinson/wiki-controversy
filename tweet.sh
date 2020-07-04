source venv/bin/activate
source keys.env

# Retry up to 10 times
for _ in {1..10}; do
  python main.py && break
  sleep 3;
done
