import asyncio
import requests
import json


class GraphQL:
    endpoint_url = 'http://localhost:8000/api/graphql'  # TODO static val, singleton으로 최초 instance 생성시 셋팅하게 처리

    @classmethod
    async def execute_async(cls, query, param={}):
        from gql import Client, gql
        from gql.transport.aiohttp import AIOHTTPTransport

        transport = AIOHTTPTransport(url=cls.endpoint_url)

        # Using `async with` on the client will start a connection on the transport
        # and provide a `session` variable to execute queries on this connection
        async with Client(
            transport=transport, fetch_schema_from_transport=True,
        ) as session:

            result = await session.execute(gql(query), variable_values=param)
            # print(result)
            return result

    @classmethod
    def execute(cls, query, param={}):
        return asyncio.run(cls.execute_async(query, param))


# REST는 이렇게 씌울 필요가 있을까, 그냥 requests에서 바로 가져다 쓰는 것은...
class REST:
    api_url = 'http://localhost:8000/api'   # TODO static val, singleton으로 최초 instance 생성시 셋팅하게 처리

    @classmethod
    def get(cls, url):
        res = requests.get(cls.api_url + url)
        if res.status_code == 200:
            obj = json.loads(res.text)
            print(obj)
            return obj
        else:
            return ''  # TODO 에러 발생시켜야 함

    @classmethod
    def post(cls, url, param):
        res = requests.post(cls.api_url + url, data=param)
        print(res)
