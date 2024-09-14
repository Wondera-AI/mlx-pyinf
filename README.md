# MNIST Demo of MLX

## Install/Update the MLX client
```bash
curl -sSL https://raw.githubusercontent.com/Wondera-AI/mlx-client/main/install.sh | bash
```

## Test Service locally using
```bash
mlx serve run               # to run all tests

mlx serve run test_foo      # to run specific test
```

Define these tests in the mlx.toml

```toml
[test.foo_test]
path_image = "src/mnist/dummy_data/image_0.png"
path_model = "src/mnist/pretrained/test_mnist.pt"
```

## Deploy Service to compute cluster

Check and adjust configuration in **mlx.toml** as required
- name the service
- deploy to "dev" or "prod" compute
- configure resources

Then deploy it

```bash
mlx serve deploy
```

## General Call the Service endpoint
```bash
curl -X POST "3.132.162.86:30000/handle_request/mnist" \
-H "Content-Type: application/json" \
-d '{
    "path_image": "src/mnist/dummy_data/image_0.png",
    "path_model": "src/mnist/pretrained/test_mnist.pt"
}'
```
Notice
- the service name and data you pass
- the data for your service
- the return is synchronous with a Job_ID

## (TEMP) Jobs and logs observability
```txt
http://3.132.162.86:30000/logs/mnist/e5e73782-e634-4bed-8c4b-0b6f5f41dae1
```
Notice
- use /[JobID]

## (N/A) Jobs and logs observability
```bash 
mlx serve jobs mnist            # view jobs for IDs

mlx serve logs mnist [Job_ID]   # view job results
```

## (N/A) Test Call the Service endpoint
```
mlx serve run test_foo --call
```
