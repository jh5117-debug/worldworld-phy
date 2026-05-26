def markdown_metric_table(rows: list[dict]) -> str:
    header='| split | metric | value |\n|---|---:|---:|'
    body=['| {split} | {metric} | {value} |'.format(**r) for r in rows]
    return '\n'.join([header]+body)
