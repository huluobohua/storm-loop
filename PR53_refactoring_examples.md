# PR #53 Refactoring Examples for Sandi Metz Compliance

## 1. Refactoring `CrossrefService._fetch_with_retry` (12 lines → multiple 5-line methods)

### Current Code (VIOLATES 5-line rule):
```python
async def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    attempt = 0
    while True:
        try:
            session = await self._safe_session()
            if session:
                return await self._fetch_async(session, url, params)
            return await self._fetch_sync(url, params)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # pragma: no cover - network errors
            await self._handle_error(url, e)
            attempt += 1
            if attempt >= 3 or not self.breaker.should_allow_request():
                break
            await asyncio.sleep(2 ** attempt)
    return {}
```

### Refactored Code (Sandi Metz Compliant):
```python
async def _fetch_with_retry(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    for attempt in range(3):
        result = await self._attempt_fetch(url, params)
        if result is not None:
            return result
        if not await self._should_retry(attempt):
            break
    return {}

async def _attempt_fetch(self, url: str, params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    try:
        return await self._fetch_with_fallback(url, params)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        await self._handle_error(url, e)
        return None

async def _fetch_with_fallback(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    session = await self._safe_session()
    if session:
        return await self._fetch_async(session, url, params)
    return await self._fetch_sync(url, params)

async def _should_retry(self, attempt: int) -> bool:
    if not self.breaker.should_allow_request():
        return False
    await asyncio.sleep(2 ** attempt)
    return True
```

## 2. Refactoring `CrossrefRM.forward` (9 lines → multiple 5-line methods)

### Current Code (VIOLATES 5-line rule):
```python
def forward(self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] | None = None) -> List[Dict[str, Any]]:
    queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
    self.usage += len(queries)
    exclude_urls = exclude_urls or []

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(self._search_all(queries))

    collected = [
        self._build_result(item)
        for items in results
        for item in items
        if self._include(f"https://doi.org/{item.get('DOI')}" if item.get('DOI') else "", exclude_urls)
    ]
    collected.sort(key=lambda r: r.get("score", 0), reverse=True)
    return collected[: self.k] if self.k else collected
```

### Refactored Code (Sandi Metz Compliant):
```python
def forward(self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] | None = None) -> List[Dict[str, Any]]:
    queries = self._prepare_queries(query_or_queries)
    self._track_usage(queries)
    raw_results = self._fetch_all_results(queries)
    filtered_results = self._filter_and_transform(raw_results, exclude_urls or [])
    return self._sort_and_limit(filtered_results)

def _prepare_queries(self, query_or_queries: Union[str, List[str]]) -> List[str]:
    if isinstance(query_or_queries, str):
        return [query_or_queries]
    return query_or_queries

def _track_usage(self, queries: List[str]) -> None:
    self.usage += len(queries)

def _fetch_all_results(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(self._search_all(queries))

def _filter_and_transform(self, results: List[List[Dict[str, Any]]], exclude_urls: List[str]) -> List[Dict[str, Any]]:
    return [
        self._build_result(item)
        for items in results
        for item in items
        if self._should_include_item(item, exclude_urls)
    ]

def _should_include_item(self, item: Dict[str, Any], exclude_urls: List[str]) -> bool:
    doi_url = self._get_doi_url(item)
    return self._include(doi_url, exclude_urls)

def _get_doi_url(self, item: Dict[str, Any]) -> str:
    doi = item.get('DOI')
    return f"https://doi.org/{doi}" if doi else ""

def _sort_and_limit(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sorted_results = sorted(results, key=lambda r: r.get("score", 0), reverse=True)
    if self.k:
        return sorted_results[:self.k]
    return sorted_results
```

## 3. Refactoring `CrossrefRM._build_result` (9 lines → multiple 5-line methods)

### Current Code (VIOLATES 5-line rule):
```python
def _build_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
    doi = item.get("DOI")
    url = f"https://doi.org/{doi}" if doi else ""
    title = item.get("title", [""])
    if isinstance(title, list):
        title = title[0] if title else ""
    return {
        "url": url,
        "title": title,
        "description": item.get("abstract", ""),
        "snippets": [item.get("abstract", "")],
        "score": self.scorer.score_source(item),
        "doi": doi,
    }
```

### Refactored Code (Sandi Metz Compliant):
```python
def _build_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "url": self._extract_url(item),
        "title": self._extract_title(item),
        "description": self._extract_abstract(item),
        "snippets": [self._extract_abstract(item)],
        "score": self.scorer.score_source(item),
        "doi": item.get("DOI"),
    }

def _extract_url(self, item: Dict[str, Any]) -> str:
    doi = item.get("DOI")
    if doi:
        return f"https://doi.org/{doi}"
    return ""

def _extract_title(self, item: Dict[str, Any]) -> str:
    title = item.get("title", [""])
    if isinstance(title, list):
        return title[0] if title else ""
    return title

def _extract_abstract(self, item: Dict[str, Any]) -> str:
    return item.get("abstract", "")
```

## 4. Decomposing `CrossrefService` Class

### Current Structure (100+ lines, multiple responsibilities):
```python
class CrossrefService:
    # Handles: caching, rate limiting, circuit breaking, HTTP requests, retries
```

### Refactored Structure (Single Responsibility):
```python
# New file: rate_limiter.py
class RateLimiter:
    def __init__(self, interval: float = 3.6):
        self._interval = interval
        self._last_request = 0.0
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self) -> None:
        async with self._lock:
            wait_time = self._calculate_wait_time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_request = time.time()
    
    def _calculate_wait_time(self) -> float:
        elapsed = time.time() - self._last_request
        return max(0, self._interval - elapsed)

# New file: http_fetcher.py
class HttpFetcher:
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager
    
    async def fetch(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        session = await self._get_session()
        if session:
            return await self._fetch_async(session, url, params)
        return await self._fetch_sync(url, params)
    
    async def _get_session(self) -> Optional["aiohttp.ClientSession"]:
        try:
            return await self.conn_manager.get_session()
        except RuntimeError:
            return None
    
    async def _fetch_async(self, session, url, params) -> Dict[str, Any]:
        async with session.get(url, params=params, timeout=10) as resp:
            resp.raise_for_status()
            return await resp.json()
    
    async def _fetch_sync(self, url, params) -> Dict[str, Any]:
        # Implementation here (5 lines max)
        pass

# Refactored crossref_service.py
class CrossrefService:
    BASE_URL = "https://api.crossref.org/works"
    JOURNAL_URL = "https://api.crossref.org/journals"
    
    def __init__(self, config: CrossrefConfig | None = None):
        config = config or CrossrefConfig()
        self._setup_services(config)
    
    def _setup_services(self, config: CrossrefConfig) -> None:
        self.cache = config.cache or CacheService(ttl=config.ttl)
        self.rate_limiter = RateLimiter(config.rate_limit_interval)
        self.fetcher = HttpFetcher(config.conn_manager or ConnectionManager())
        self.breaker = config.breaker or CircuitBreaker()
    
    async def search_works(self, query: str, limit: int = 5) -> list[Dict[str, Any]]:
        params = {"query": query, "rows": limit}
        data = await self._fetch_with_cache(self.BASE_URL, params)
        return self._extract_items(data)
    
    def _extract_items(self, data: Dict[str, Any]) -> list[Dict[str, Any]]:
        message = data.get("message", {})
        return message.get("items", [])
    
    async def _fetch_with_cache(self, url: str, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        cached = await self._get_from_cache(url, params)
        if cached:
            return cached
        return await self._fetch_and_cache(url, params)
    
    # Additional refactored methods follow the 5-line rule...
```

## 5. Creating Value Objects to Replace Primitive Obsession

### Current Code (Dict[str, Any] everywhere):
```python
def forward(self, query_or_queries, exclude_urls=None) -> List[Dict[str, Any]]:
    # Returns generic dictionaries
```

### Refactored Code (Domain Objects):
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CrossrefResult:
    """Value object for Crossref search results."""
    url: str
    title: str
    description: str
    snippets: List[str]
    score: float
    doi: Optional[str]
    
    @classmethod
    def from_item(cls, item: Dict[str, Any], scorer: SourceQualityScorer) -> "CrossrefResult":
        return cls(
            url=cls._build_url(item),
            title=cls._extract_title(item),
            description=item.get("abstract", ""),
            snippets=[item.get("abstract", "")],
            score=scorer.score_source(item),
            doi=item.get("DOI")
        )
    
    @staticmethod
    def _build_url(item: Dict[str, Any]) -> str:
        doi = item.get("DOI")
        return f"https://doi.org/{doi}" if doi else ""
    
    @staticmethod
    def _extract_title(item: Dict[str, Any]) -> str:
        title = item.get("title", [""])
        if isinstance(title, list):
            return title[0] if title else ""
        return title

# Updated CrossrefRM
class CrossrefRM(dspy.Retrieve):
    def forward(self, query_or_queries, exclude_urls=None) -> List[CrossrefResult]:
        # Now returns typed domain objects
        pass
```

## Summary of Refactoring Benefits

1. **Readability**: Each method now has a single, clear purpose
2. **Testability**: Small methods are easier to test in isolation
3. **Maintainability**: Changes are localized to specific methods
4. **Reusability**: Extracted methods can be reused across the codebase
5. **Type Safety**: Domain objects provide better type checking than dictionaries