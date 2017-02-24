from aioes import Elasticsearch
from aioes.client import IndicesClient
import ujson


class ElSearchBind(object):

    def __init__(self, host, index, port=9200, loop=None):
        self._client = Elasticsearch(['{}:{}'.format(host, port)], loop=loop)
        self._index = index

    async def search(self, doc_type, pattern, page, size):
        return await self._client.search(
            index=self._index,
            doc_type=doc_type,
            body={
                'query': {
                    'match': {'_all': pattern}
                },
                'from': page,
                'size': size
            }
        )

    async def bulk_update_dict(self, doc_type, dict_):
        return await self._bulk_dict(doc_type, dict_, 'update')

    async def _bulk_dict(self, doc_type, dict_, type_):
        body = []
        for key, value in dict_.items():
            key = key.decode() if isinstance(key, bytes) else key
            body.append({type_: {'_id': key}})
            value = ujson.loads(value)

            if type_ == 'update':
                body.append({'doc': value})
            elif type_== 'create':
                body.append(value)

        return await self._client.bulk(body, index=self._index, doc_type=doc_type)

    async def bulk_create_dict(self, doc_type, dict_):
        return await self._bulk_dict(doc_type, dict_, 'create')

    async def bulk_delete(self, doc_type, keys):
        body = [
            {'delete': {'_id': key.decode() if isinstance(key, bytes) else key}}
                for key in keys]
        return await self._client.bulk(body, index=self._index, doc_type=doc_type)

    def close(self):
        self._client.close()

    def __del__(self):
        self.close()

    async def create_index(self):
        if not (await self._client.indices.exists(self._index)):
            await self._client.indices.create(self._index)

    async def refresh_index(self):
        if await self._client.indices.exists(self._index):
            await self._client.indices.refresh(self._index)

    async def flush_index(self):
        if await self._client.indices.exists(self._index):
            await self._client.indices.flush(self._index)
