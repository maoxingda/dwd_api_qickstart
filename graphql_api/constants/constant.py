from enum import Enum


TABLE_NAME_REGEXP = r'^[a-z][_a-z0-9]{4,}$'


class TableTypes(Enum):
    DWD = '事实表'
    DIM = '维度表'


class JoinTypes(Enum):
    INNER_JOIN = 'inner join'
    LEFT_JOIN = 'left join'
    RIGHT_JOIN = 'right join'
    FULL_JOIN = 'full join'
