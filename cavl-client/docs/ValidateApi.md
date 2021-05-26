# cavl_client.ValidateApi

All URIs are relative to _https://cavl.api.itoworld.com/v0_

| Method                                            | HTTP request       | Description                                  |
| ------------------------------------------------- | ------------------ | -------------------------------------------- |
| [**validate_feed**](ValidateApi.md#validate_feed) | **POST** /validate | Creates a validation task to validate a feed |

# **validate_feed**

> ValidationTaskResult validate_feed(body)

Creates a validation task to validate a feed

### Example

```python
from __future__ import print_function
import time
import cavl_client
from cavl_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = cavl_client.ValidateApi()
body = cavl_client.ValidationTaskResult() # ValidationTaskResult | ValidationTaskResult object that indicates the validity of the feed

try:
    # Creates a validation task to validate a feed
    api_response = api_instance.validate_feed(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling ValidateApi->validate_feed: %s\n" % e)
```

### Parameters

| Name     | Type                                                | Description                                                         | Notes |
| -------- | --------------------------------------------------- | ------------------------------------------------------------------- | ----- |
| **body** | [**ValidationTaskResult**](ValidationTaskResult.md) | ValidationTaskResult object that indicates the validity of the feed |

### Return type

[**ValidationTaskResult**](ValidationTaskResult.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
