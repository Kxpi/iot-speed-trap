# Lambda e-mail function 
Code is trigerred by an event from IoT rule when there is a specific field defined in an incoming MQTT message:
```sql
SELECT * FROM '<TOPIC_NAME>' WHERE IsUndefined(ticket_file) = False
```
It's task is to take apropriate picture from S3 and to create an e-mail with ticket. The e-mail is then sent automatically using Amazon SES.

## Tariff
JSON file contains costs and number of penalty points for speeding driver. The number which works as a key is upper border of the range. For example:

| Speed over limit  |  Cost | Points  |
|--------|------|-----|
| 1-10   | 100  | 2  |
| 11-20  | 300  | 4  |
| 21-30  | 500  | 6  |
| 31-40  | 800  | 12 |
| 41-50  | 1500 | 24 |

Values that correspond to given keys are calculated by function below:

```python
def round_up(num):
    return math.ceil(num / 10) * 10
```

Basically all it does is rounding to upper 10 giving appropriate key for tariff. \
For example: \
``` Speed over limit = 27 ``` \
Rounded up is 30, which is a key for penalty for going 21-30km/h above speed limit.

### For **really** fast drivers which go even above the last category, there is a special variable declared with the highest penalty. It's used when the get() method can't find key in **tariff** dict.
```python
MAX_TARIFF = {
    'cost': 3000,
    'points': 24
}
```