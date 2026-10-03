"""Read the modern Power BI DAX Arrow response, including HTTP-200 errors."""
import io


def arrow_rows(raw):
    import pyarrow as pa
    stream = io.BytesIO(raw)
    results = []
    while stream.tell() < len(raw):
        before = stream.tell()
        reader = pa.ipc.open_stream(stream)
        table = reader.read_all()
        metadata = {key.decode().lower(): value.decode() for key, value in (reader.schema.metadata or {}).items()}
        if metadata.get("iserror", "").lower() == "true":
            raise RuntimeError("DAX error: " + metadata.get("faultstring", str(table.to_pylist())))
        results.append(table.to_pylist())
        if stream.tell() <= before:
            raise ValueError("Arrow reader did not advance")
    if len(results) != 1 or len(results[0]) != 1:
        raise ValueError("Expected one DAX rowset with one KPI row")
    return results[0]
