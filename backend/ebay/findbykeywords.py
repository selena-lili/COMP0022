from ebaysdk.finding import Connection

if __name__ == '__main__':
    api = Connection(config_file='../ebay.yaml', siteid="EBAY-GB")

    request = {
        'keywords': 'rings',
        'itemFilter': [
            {'name': 'condition', 'value': 'new'}
        ],
        'paginationInput': {
            'entriesPerPage': 10,
            'pageNumber': 1
        },
        'sortOrder': 'PricePlusShippingLowest'
    }

    response = api.execute('findItemsByKeywords', request)

    for item in response.reply.searchResult.item:
        print(f"Title: {item.title}, Price: {item.sellingStatus.currentPrice.value}\n")