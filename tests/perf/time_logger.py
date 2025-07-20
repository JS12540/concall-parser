import asyncio
import os
import time
from dataclasses import dataclass

from concall_parser.log_config import logger
from concall_parser.utils import file_utils


@dataclass
class BenchmarkResult:
    """Structured benchmark result."""

    func_name: str
    duration: float
    mode: str  # 'sync' or 'async'
    input_identifier: str  # identifier for the specific input used
    arg_count: int
    kwarg_count: int
    success: bool
    error_message: str | None = None
    timestamp: float = None

    def __post_init__(self):
        """Override post init for benchmark results."""
        if self.timestamp is None:
            self.timestamp = time.time()


class Benchmark:
    """Benchmark function performance with respect to time for measuring improvments."""

    def __init__(self):
        self.results = []

    def time_sync(self, func, *args, **kwargs):
        """Time a synchronous function call."""
        start_time = time.perf_counter()
        exec_result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        result = {
            "func": func.__name__,
            "duration": duration,
            "mode": "sync",
            "arg_count": len(args),
            "kwarg_count": len(kwargs),
        }

        logger.info(f"Executed sync func {func.__name__}", extra=result)
        self.results.append(result)
        return exec_result

    async def time_async(self, func, *args, **kwargs):
        """Time an asynchronous function."""
        start_time = time.perf_counter()
        exec_result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        result = {
            "func": func.__name__,
            "duration": duration,
            "mode": "async",
            "arg_count": len(args),
            "kwarg_count": len(kwargs),
        }
        logger.info(f"Executed async func {func.__name__}", extra=result)
        self.results.append(result)
        return exec_result

    def print_results(self):
        """Prints benchmark results."""
        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)

        for result in self.results:
            print(f"Function: {result['func']}")
            print(f"Duration: {result['duration']:.4f} seconds")
            print(f"Args: {result['arg_count']}, Kwargs: {result['kwarg_count']}")
            print("-" * 40)

    def get_average_time(self, function_name: str) -> float:
        """Get average time for a specific function."""
        times = [r["duration"] for r in self.results if r["function"] == function_name]
        return sum(times) / len(times) if times else 0

    async def run_batch_benchmark(self, func, times: int, *args, **kwargs):
        """Run the benchmark multiple times to check average performance."""
        if not times:
            times = 5
        durations = []
        for _ in range(times):
            start_time = time.perf_counter()
            if hasattr(func, "__await__"):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            end_time = time.perf_counter()
            durations.append(end_time - start_time)
        avg_duration = sum(durations) / len(durations) if durations else 0
        logger.info(
            f"Batch benchmark for {func.__name__}: avg {avg_duration:.4f}s over {times} runs"
        )
        return avg_duration


async def run_file_utils_perf():
    """Benchmarking for file util functions defined in concall_parser/utils/file_utils.py."""
    benchmark = Benchmark()
    test_documents_dir = "tests/test_documents"
    test_links = [
        "https://www.adanigas.com/-/media/Project/AdaniGas/Investors/Financials/Earnings-Call-Transcript-and--Recordings/AdaniTotalGas-Earnings-Q3FY25.pdf",
        "https://www.indusind.com/content/dam/indusind-corporate/investors/QuarterFinancialResults/FY2024-2025/Quarter4/IndusInd-Bank-Analyst-Call-Q4FY25-20250521.pdf",
        "https://www.bseindia.com/stockinfo/AnnPdfOpen.aspx?Pname=a809b7d3-ca44-4410-acf7-af064786fe5a.pdf",
    ]
    test_files = [
        os.path.join(test_documents_dir, f)
        for f in os.listdir(test_documents_dir)
        if f.endswith(".pdf")
    ]

    transcripts = []

    # Test get_doc_transcript (path)
    for file_path in test_files:
        try:
            transcript = await benchmark.time_async(
                file_utils.get_document_transcript, file_path
            )
            transcripts.append(transcript)
        except Exception:
            logger.exception(f"Error in get_document_transcript for {file_path}")

    # Test get_transcript_from_link
    for link in test_links:
        try:
            transcript = await benchmark.time_async(file_utils.get_transcript_from_link, link)
            transcripts.append(transcript)
        except Exception:
            logger.error(f"Error in get_transcript_from_link for {link}")

    # TODO: benchmarking for save_output

    # Test save_transcript (async)
    for i, transcript in enumerate(transcripts):
        try:
            await benchmark.time_async(
                file_utils.save_transcript, transcript, "sample.pdf", "test_perf"
            )
        except Exception as e:
            logger.error(f"Error in save_transcript for {test_files[i]}: {e}")

    benchmark.print_results()


asyncio.run(run_file_utils_perf())
