import pytest
from app.engine import evaluate
from app.config import ROOT
@pytest.fixture
def sample():
    return evaluate()
@pytest.fixture
def clean():
    return evaluate({'dataset':'clean'})
@pytest.fixture
def conflict_csv():
    text=(ROOT/'sample_data/clean.csv').read_text()
    lines=[line for line in text.splitlines() if not line.startswith('00001-R1,')]
    # 同一首次结果 00001-V1 的两条有效复检：R9 采样更晚但版本低，R8 采样更早但版本高，数值不同。
    lines.append('00001-R9,00001,V1,2026-10-10T08:00:00+08:00,2026-10-01T00:00:00+08:00,RETEST,00001-V1,130,mg/dL,auto,2')
    lines.append('00001-R8,00001,V1,2026-10-09T12:00:00+08:00,2026-10-01T00:00:00+08:00,RETEST,00001-V1,125,mg/dL,auto,3')
    return '\n'.join(lines)+'\n'
@pytest.fixture
def conflict(conflict_csv):
    return evaluate({'csv_text':conflict_csv})
