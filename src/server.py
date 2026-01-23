from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import Response 
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST as PROMETHEUS_CONTENT_TYPE
from datetime import datetime
import time

from .config.settings import settings
from .config.logger import logger
from .models import (
    AnalysisRequest,
    AnalysisResult,
    OptimizationRequest,
    OptimizationResult,
    HealthResponse,
)
from .analyzers import HybridAnalyzer
from .cache import cache_manager
from .utils.token_counter import token_counter


# Prometheus metrics
analysis_requests = Counter('prompt_analysis_requests_total', 'Total analysis requests')
optimization_requests = Counter('prompt_optimization_requests_total', 'Total optimization requests')
analysis_duration = Histogram('prompt_analysis_duration_seconds', 'Analysis duration')
cache_hits = Counter('cache_hits_total', 'Cache hits')
cache_misses = Counter('cache_misses_total', 'Cache misses')


# Global analyzer instance
analyzer = HybridAnalyzer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting PromptAssist API...")
    await cache_manager.connect()
    logger.info("✅ Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down PromptAssist API...")
    await cache_manager.disconnect()
    logger.info("✅ Application shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="PromptAssist API",
    description="AI-powered prompt analysis and optimization service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"➡️  {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    logger.info(
        f"⬅️  {request.method} {request.url.path} "
        f"- {response.status_code} ({duration:.3f}s)"
    )
    
    return response


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    logger.error(f"❌ Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    redis_connected = await cache_manager.is_connected()
    
    return HealthResponse(
        status="healthy" if redis_connected or not settings.cache_enabled else "degraded",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        redis_connected=redis_connected
    )


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=PROMETHEUS_CONTENT_TYPE)


# Analysis endpoint
@app.post("/api/prompt/analyze", response_model=AnalysisResult)
async def analyze_prompt(request: AnalysisRequest):
    """
    Analyze a prompt and return issues and quality score.
    
    Args:
        request: Analysis request with prompt text
        
    Returns:
        Analysis results including issues, quality score, and token count
    """
    analysis_requests.inc()
    start_time = time.time()
    
    try:
        # Validate prompt length
        if len(request.text) > settings.max_prompt_length:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt exceeds maximum length of {settings.max_prompt_length} characters"
            )
        
        if len(request.text) < settings.min_prompt_length:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt must be at least {settings.min_prompt_length} characters"
            )
        
        # Check cache
        cache_key = cache_manager.generate_key(
            "analysis",
            request.text,
            use_llm=request.use_llm
        )
        cached = await cache_manager.get(cache_key)
        
        if cached:
            cache_hits.inc()
            logger.info("✅ Returning cached analysis result")
            return AnalysisResult(**cached)
        
        cache_misses.inc()
        
        # Perform analysis
        logger.info(f"Analyzing prompt (LLM: {request.use_llm})...")
        issues = await analyzer.analyze(request.text, use_llm=request.use_llm)
        
        # Calculate metrics
        quality_score = analyzer.calculate_quality_score(request.text, issues)
        token_count = token_counter.count_tokens(request.text)
        estimated_improvement = max(0, 100 - quality_score)
        
        # Create result
        result = AnalysisResult(
            issues=issues,
            quality_score=quality_score,
            token_count=token_count,
            estimated_improvement=estimated_improvement
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.model_dump())
        
        # Record metrics
        duration = time.time() - start_time
        analysis_duration.observe(duration)
        
        logger.info(
            f"✅ Analysis complete: {len(issues)} issues, "
            f"quality={quality_score}, tokens={token_count} ({duration:.3f}s)"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Optimization endpoint
@app.post("/api/prompt/optimize", response_model=OptimizationResult)
async def optimize_prompt(request: OptimizationRequest):
    """
    Optimize a prompt using AI.
    
    Args:
        request: Optimization request with prompt text and parameters
        
    Returns:
        Optimized prompt with improvements and metrics
    """
    optimization_requests.inc()
    start_time = time.time()
    
    try:
        # Validate prompt length
        if len(request.text) > settings.max_prompt_length:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt exceeds maximum length of {settings.max_prompt_length} characters"
            )
        
        if not settings.enable_llm_analysis:
            raise HTTPException(
                status_code=503,
                detail="LLM optimization is currently disabled"
            )
        
        # Check cache
        cache_key = cache_manager.generate_key(
            "optimization",
            request.text,
            focus=request.focus.value,
            level=request.level.value
        )
        cached = await cache_manager.get(cache_key)
        
        if cached:
            cache_hits.inc()
            logger.info("✅ Returning cached optimization result")
            return OptimizationResult(**cached)
        
        cache_misses.inc()
        
        # Get before score
        logger.info("Analyzing original prompt...")
        before_issues = await analyzer.analyze(request.text, use_llm=False)
        before_score = analyzer.calculate_quality_score(request.text, before_issues)
        before_tokens = token_counter.count_tokens(request.text)
        
        # Optimize
        logger.info(f"Optimizing prompt (focus={request.focus}, level={request.level})...")
        optimization = await analyzer.llm_optimizer.optimize_prompt(
            request.text,
            focus=request.focus.value,
            level=request.level.value
        )
        
        # Get after score
        optimized_text = optimization.get("optimized_prompt", request.text)
        after_issues = await analyzer.analyze(optimized_text, use_llm=False)
        after_score = analyzer.calculate_quality_score(optimized_text, after_issues)
        after_tokens = token_counter.count_tokens(optimized_text)
        
        # Create result
        result = OptimizationResult(
            optimized_prompt=optimized_text,
            improvements=optimization.get("improvements", []),
            token_savings=before_tokens - after_tokens,
            quality_improvement=after_score - before_score,
            before_score=before_score,
            after_score=after_score
        )
        
        # Cache result
        await cache_manager.set(cache_key, result.model_dump(), ttl=7200)  # 2 hours
        
        duration = time.time() - start_time
        logger.info(
            f"✅ Optimization complete: {before_score}→{after_score}, "
            f"tokens: {before_tokens}→{after_tokens} ({duration:.3f}s)"
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Optimization failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Clear cache endpoint (admin)
@app.delete("/api/cache/clear")
async def clear_cache(pattern: str = "*"):
    """Clear cache entries (admin endpoint)."""
    try:
        await cache_manager.clear_pattern(pattern)
        return {"message": f"Cache cleared for pattern: {pattern}"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
