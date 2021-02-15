from time import time


class ExtDict(dict):
    """dict클래스를 확장한 클래스로 accutuning-client에서는 이 클래서 상속받아 사용"""
    def __init__(self, *args, dict_obj=None, **kwargs):
        super().__init__(*args, **kwargs)
        if dict_obj:
            super().update(dict_obj)  # timestamp setting 로직 중복을 방지하려고 super()에 있는 update 호출
        self._update_timestamp()

    def _update_timestamp(self):
        """객체의 timestamp정보를 업데이트함"""
        self._timestamp = time()

    def get(self, k, *args):
        """여러 Depth의 get을 한꺼번에 실행함(key안에 "."으로 구분)"""
        if isinstance(k, str) and '.' in k:
            obj = super()
            try:
                for sub_key in k.split('.'):
                    obj = obj.get(sub_key, *args)
            except Exception:
                obj = None
            return obj
        else:
            return super().get(k, *args)

    def __getitem__(self, k):
        """여러 Depth의 get을 한꺼번에 실행함(key안에 "."으로 구분)"""
        if isinstance(k, str) and '.' in k:
            obj = super()
            try:
                for sub_key in k.split('.'):
                    obj = obj.__getitem__(sub_key)
            except Exception:
                raise KeyError(k)
            return obj
        else:
            return super().__getitem__(k)

    def update(self, *args):
        """dict의 update method"""
        super().update(*args)
        self._update_timestamp()
