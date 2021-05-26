# cavl_client.FeedApi

All URIs are relative to _https://cavl.api.itoworld.com/v0_

| Method                                                        | HTTP request              | Description                                                   |
| ------------------------------------------------------------- | ------------------------- | ------------------------------------------------------------- |
| [**add_feed**](FeedApi.md#add_feed)                           | **POST** /feed            | Adds a new feed                                               |
| [**delete_feed**](FeedApi.md#delete_feed)                     | **DELETE** /feed/{feedId} | Deletes the feed with the specified ID                        |
| [**get_feed**](FeedApi.md#get_feed)                           | **GET** /feed/{feedId}    | Gets a feed by ID                                             |
| [**get_feeds**](FeedApi.md#get_feeds)                         | **GET** /feed             | Gets a list of feeds                                          |
| [**update_feed_with_form**](FeedApi.md#update_feed_with_form) | **POST** /feed/{feedId}   | Updates an existing feed with the specified ID with form data |

# **add_feed**

> InlineResponse201 add_feed(body)

Adds a new feed

### Example

```python
from __future__ import print_function
import time
import cavl_client
from cavl_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = cavl_client.FeedApi()
body = cavl_client.Feed() # Feed | Feed object that needs to be added to the consumer config

try:
    # Adds a new feed
    api_response = api_instance.add_feed(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FeedApi->add_feed: %s\n" % e)
```

### Parameters

| Name     | Type                | Description                                               | Notes |
| -------- | ------------------- | --------------------------------------------------------- | ----- |
| **body** | [**Feed**](Feed.md) | Feed object that needs to be added to the consumer config |

### Return type

[**InlineResponse201**](InlineResponse201.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_feed**

> delete_feed(feed_id)

Deletes the feed with the specified ID

### Example

```python
from __future__ import print_function
import time
import cavl_client
from cavl_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = cavl_client.FeedApi()
feed_id = 56 # int | The ID of the feed to delete

try:
    # Deletes the feed with the specified ID
    api_instance.delete_feed(feed_id)
except ApiException as e:
    print("Exception when calling FeedApi->delete_feed: %s\n" % e)
```

### Parameters

| Name        | Type    | Description                  | Notes |
| ----------- | ------- | ---------------------------- | ----- |
| **feed_id** | **int** | The ID of the feed to delete |

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feed**

> Feed get_feed(feed_id)

Gets a feed by ID

Returns a single feed config

### Example

```python
from __future__ import print_function
import time
import cavl_client
from cavl_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = cavl_client.FeedApi()
feed_id = 56 # int | The ID of feed to return

try:
    # Gets a feed by ID
    api_response = api_instance.get_feed(feed_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FeedApi->get_feed: %s\n" % e)
```

### Parameters

| Name        | Type    | Description              | Notes |
| ----------- | ------- | ------------------------ | ----- |
| **feed_id** | **int** | The ID of feed to return |

### Return type

[**Feed**](Feed.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_feeds**

> list[Feed] get_feeds()

Gets a list of feeds

### Example

```python
from __future__ import print_function
import time
import cavl_client
from cavl_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = cavl_client.FeedApi()

try:
    # Gets a list of feeds
    api_response = api_instance.get_feeds()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FeedApi->get_feeds: %s\n" % e)
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**list[Feed]**](Feed.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_feed_with_form**

> update_feed_with_form(feed_id, body=body)

Updates an existing feed with the specified ID with form data

### Example

```python
from __future__ import print_function
import time
import cavl_client
from cavl_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = cavl_client.FeedApi()
feed_id = 56 # int | The ID of feed to update
body = cavl_client.Body() # Body |  (optional)

try:
    # Updates an existing feed with the specified ID with form data
    api_instance.update_feed_with_form(feed_id, body=body)
except ApiException as e:
    print("Exception when calling FeedApi->update_feed_with_form: %s\n" % e)
```

### Parameters

| Name        | Type                | Description              | Notes      |
| ----------- | ------------------- | ------------------------ | ---------- |
| **feed_id** | **int**             | The ID of feed to update |
| **body**    | [**Body**](Body.md) |                          | [optional] |

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)
