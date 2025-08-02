
async def getDataSixMonth(cust_no,db):
    data = await db.fetch("SELECT DISTINCT ON (no_trans_lending) * FROM gateway.lending_data WHERE cust_no = $1 and tanggal_trans between '2024-06-01' and '2024-12-31' " \
    "ORDER BY no_trans_lending, tanggal_trans ASC", cust_no)
    print(data)
    if not data:
        return {
            'responseStatus':404,
            'message': 'Data not found'
        }
    else:
        return {
            'responseStatus':201,
            'message': 'Get Data successfully',
            'data':data
        }