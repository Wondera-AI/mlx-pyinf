# MNIST Demo of MLX

## Install the MLX client
```
curl -sSL https://raw.githubusercontent.com/Wondera-AI/mlx-client/main/install.sh | bash
```

## Test Service locally for now using
```
pdm run main
```
To start the service and then use this to call it:
```
redis-cli -h redis-17902.c322.us-east-1-2.ec2.redns.redis-cloud.com -p 17902 -a "MkiTVpOWFVLGLgJ7ptZ29dY80zER4cvR" PUBLISH "test-channel" "{\"request_data\":\"{\\\"body\\\":{\\\"path_image\\\":\\\"src/mnist/dummy_data/image_0.png\\\",\\\"optional_smoothing\\\":20}}\",\"publish_channel\":\"test-channel\",\"response_channel\":\"py_service:a3-2:output\",\"log_key\":\"test_foo\"}"
```

## Deploy Service to compute cluster
```
mlx serve deploy "mnist" --memory-limit 512Mib --concurrent-jobs 2 --cpu-limit 0.5
```

## Test request of Service prediction from the cluster
```
curl -X POST "10.100.78.199/3000/handle_request/mnist" \
-H "Content-Type: application/json" \
-d '{
    "path_image": "src/mnist/dummy_data/image_0.png",
    "optional_smoothing": 20
}'
```