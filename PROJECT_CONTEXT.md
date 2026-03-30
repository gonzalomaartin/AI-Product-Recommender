# Mercadona-LLM: Project Context Document

## 📋 Project Overview

**Mercadona-LLM** is an AI-powered product recommendation and discovery system designed to scrape, process, and intelligently search product data from Mercadona's online supermarket. The system combines web scraping, large language models (LLMs), vision language models (VLMs), and dual-database storage to provide semantic search capabilities and personalized product recommendations.

---

## 🎯 Problem Statement & Solution

### Problems Solved
1. **Manual Product Discovery**: Users must manually browse Mercadona's website to find products, which is time-consuming and inefficient.
2. **Limited Search Capabilities**: Traditional keyword-based search doesn't understand semantic intent (e.g., "healthier alternative to Nutella").
3. **Data Extraction from Images**: Nutritional information and product claims are embedded in images, requiring manual extraction.
4. **Personalized Recommendations**: No system to recommend similar products based on user preferences and constraints (price, allergens, etc.).

### What It Accomplishes
1. **Automated Product Scraping**: Extracts comprehensive product data (title, price, ingredients, images) from Mercadona's website.
2. **AI-Powered Data Enrichment**: Uses LLMs to extract and normalize brand, allergens, and product claims from descriptions.
3. **Visual Information Extraction**: Employs VLMs to parse nutritional information and claims from product images.
4. **Semantic Search**: Enables natural language queries like "I want a lactose-free drink similar to almond milk but cheaper."
5. **Dual-Database Storage**: Combines relational and vector databases for fast filtering and semantic matching.
6. **Smart Ranking**: LLMs rank products based on user preferences, price, allergens, and nutritional needs.

---

## 🏗️ Technical Architecture

### System Components

#### 1. **Web Scraping Layer** (`src/scraper/`)
- **Tool**: Playwright (async for concurrency)
- **Responsibility**: Extract product data from Mercadona's website
- **Files**:
  - `playwright_scraper.py`: Main scraping orchestrator using Playwright async API
  - `utils.py`: Utility functions for scraping tasks (download_image, resize_image_url, etc.)

- **Key Functions**:
  - `get_categories()`: Navigate and extract all product categories
  - `get_items()`: Iterate through items in a category
  - `get_item_info()`: Extract detailed product information from product detail page
  - `download_image()`: Async image download using aiohttp

- **Data Extracted**:
  - Product ID, Title, Category, Subcategory
  - Description, Price, Weight, Unit
  - Ingredients, Origin, Product Link
  - Product Images (up to 5 per product, resized to 900px)

#### 2. **AI Integration Layer** (`src/ai/`)
- **Architecture**: Class-based `AIOrchestrator` for managing AI pipelines
- **Configuration** (`config.py`):
  - `RELATIVE_PRICE_PROVIDER = "groq"` with model `llama-3.3-70b-versatile`
  - `ALLERGENS_PROVIDER = "groq"` with model `moonshotai/kimi-k2-instruct`
  - `NUTRITIONAL_INFO_PROVIDER = "google_genai"` with model `gemini-3.1-flash-lite-preview`

- **Schemas** (`schemas.py`):
  - `RelativePrice`: Pydantic model for price classification (very barato to muy caro)
  - `NutritionalInfo`: Pydantic model for nutritional data extraction
  - `Allergens`: Pydantic model for allergen identification

- **Orchestration** (`orchestrator.py`):
  - `AIOrchestrator` class: Pre-builds chains for each task in `__init__`
  - `extract_relative_price()`: LLM-based price classification
  - `extract_nutritional_info()`: VLM-based extraction from product images (dynamic message building)
  - `extract_allergens()`: LLM-based allergen extraction using Pydantic parser
  - `orchestrate_AI_pipeline()`: Runs all enabled AI tasks concurrently via `asyncio.gather()`

- **Features**:
  - Retry logic: `@retry` decorator with exponential backoff (5 attempts, 2-60s delay)
  - Structured output: Uses LangChain's `with_structured_output()` for type-safe responses
  - Dynamic image handling: Builds HumanMessage content with up to 5 images per request
  - Error handling: `return_exceptions=True` to catch and log failures without stopping pipeline

#### 3. **Database Layer** (`src/database/`)

##### Relational Database (PostgreSQL/SQLite)
- **ORM**: SQLAlchemy
- **File**: `db_utils.py`
- **Schema**: `Product` model with 30+ fields
- **Key Fields**:
  - Primary key: `ID_producto` (String)
  - Metadata: `categoria`, `subcategoria`, `titulo`, `descripcion`, `marca`, `origen`
  - Pricing: `precio`, `peso`, `precio_por_unidad`, `unidad`, `precio_relativo`
  - Nutritional: `energia_kj`, `energia_kcal`, `grasas_g`, `carbohidratos_g`, `azucar_g`, `fibra_g`, `proteina_g`, `sal_g`
  - AI-extracted: `alergenos` (JSON), `atributos` (JSON)
  - Metadata: `link_producto` (unique), `tiempo_computo` (float)
- **Purpose**: Fast indexed lookups by category, price, allergens
- **Session Management**: Synchronous operations with connection pooling (10 pool size, 20 max overflow)

##### Vector Database (Chroma)
- **Purpose**: Store embeddings for semantic search
- **Implementation**: `chromadb.PersistentClient`
- **Location**: `data/chroma_db/`
- **Model**: BAAI/bge-m3 (SentenceTransformer) for embeddings
- **Data Stored**:
  - Product ID
  - Embeddings (768-dimensional vectors)
  - Metadata

##### Database Operations (`db_operations.py`):
- `init_db()`: Initialize database schema synchronously
- `upload_product_relational_db()`: Insert product into relational DB
- `upload_product_vector_db()`: Insert embedding into Chroma
- `check_item_id()`: Check if product already exists
- `compute_embedding()`: Generate embeddings using SentenceTransformer

#### 4. **Utilities & Helpers** (`src/scraper/utils.py`)

#### 5. **Data Utilities** (`databases/`)
- `clear_vector.py`: Script to clear Chroma vector database
- `clear_relational.py`: Script to clear PostgreSQL database
- `products.csv`: Exported product data

---

## 🔄 Data Flow & Workflow

### 1. **Product Scraping Pipeline**
```
Website (Mercadona) 
    ↓ [Playwright async scraping]
Product Data (title, description, price, images)
    ↓ [get_item_info() extracts product details]
Product Information Object
    ↓ [AIOrchestrator processes]
Enriched product data with AI insights
```

### 2. **AI Enrichment Pipeline** (via `AIOrchestrator`)
```
Product Data
    ├─→ [extract_relative_price()] LLM classifies price → RelativePrice schema
    ├─→ [extract_nutritional_info()] VLM parses images → NutritionalInfo schema
    └─→ [extract_allergens()] LLM identifies allergens → Allergens schema
         ↓ [asyncio.gather combines all results]
Unified enriched product dictionary
```

### 3. **Database Storage**
```
Enriched Product Data
    ├─→ [upload_product_relational_db()] → PostgreSQL/SQLite
    ├─→ [compute_embedding()] → BAAI/bge-m3 embedding
    └─→ [upload_product_vector_db()] → Chroma
```

### 4. **Semantic Search Workflow**
```
User Query ("I want a healthier alternative to Nutella")
    ↓ [compute_embedding()] Generate embedding
Vector representation of query
    ↓ [Chroma semantic search]
Top-K similar products
    ↓ [Product ID lookup]
Detailed product info from PostgreSQL
    ↓ [Optional: Re-rank with LLM]
Ranked recommendations
```

---

## 📦 Dependencies & Technologies

### Core Technologies
- **Python 3.9+**: Language
- **Playwright**: Async browser automation for web scraping
- **LangChain**: LLM orchestration and chain management
- **SQLAlchemy**: ORM for relational database
- **PostgreSQL/SQLite**: Relational database
- **Chroma**: Vector database with persistent storage
- **Groq API**: LLM and VLM inference (primary)
- **Google Gemini API**: VLM for nutritional information
- **Tenacity**: Retry logic with exponential backoff
- **Pydantic**: Data validation and schema definition
- **asyncio**: Asynchronous programming
- **aiohttp, aiofiles**: Async HTTP and file I/O
- **SentenceTransformer**: Embeddings generation (BAAI/bge-m3)

### Key Libraries
- `dotenv`: Environment variable management
- `pandas`: Data manipulation (evaluation scripts)
- `aiohttp`: Async HTTP client for image downloads
- `chromadb`: Vector database client
- `tenacity`: Retry decorator with exponential backoff

### Environment Variables (`.env`)
```
DATABASE_URL=postgresql://user:password@localhost/db
GROQ_API_KEY=your_groq_api_key
GROQ_LLM=llama-3.3-70b-versatile
GROQ_VLM=vision_model_name
GOOGLE_API_KEY=your_google_api_key
COLLECTION_NAME=products_embeddings
```

---

## 📊 Current State of the Project

### ✅ Completed Features
1. **Web Scraping**: Functional async Playwright scraper for Mercadona products
2. **AI Orchestration**: Class-based `AIOrchestrator` for managing multiple AI tasks
3. **LLM Integration**: 
   - Price classification (Groq's llama-3.3-70b)
   - Allergen extraction (Groq's kimi-k2-instruct)
   - Structured output with Pydantic validation
4. **VLM Integration**: 
   - Nutritional information extraction from product images (Google Gemini)
   - Dynamic image handling with up to 5 images per request
5. **Dual Database**: PostgreSQL/SQLite for structured data, Chroma for semantic search
6. **Error Handling**: Exponential backoff retry logic with Tenacity decorator
7. **Evaluation Framework**: Automated evaluation system with metrics calculation
8. **Testing Suite**: test_ai.py, test_scraper.py for validation

### 🔄 Recent Changes (March 2026)
1. **Refactored AI Pipeline**: Moved from functional to class-based `AIOrchestrator` design
2. **LangChain Integration**: Replaced custom API calls with LangChain's standardized interface
3. **Dynamic Image Handling**: Fixed image passing by building HumanMessage content dynamically
4. **Retry Decorator**: Added `@retry` decorator with exponential backoff (5 attempts, 2-60s delay)
5. **Provider Configuration**: Separated model providers (Groq, Google, Moonshot)
6. **Error Handling**: Improved error logging with task names and exception details

### 🚀 Working Features
- ✅ Product scraping from Mercadona with Playwright
- ✅ LLM-based price classification and allergen extraction
- ✅ VLM-based nutritional information extraction from images
- ✅ Async database operations with SQLAlchemy
- ✅ Vector embeddings with SentenceTransformer
- ✅ Semantic search via Chroma
- ✅ Comprehensive error handling and retry logic
- ✅ Evaluation and metrics calculation

### ⚠️ Known Issues / Limitations
1. **Image Content Passing**: Images must be deserialized (unpacked with `*`) for proper VLM processing
2. **Rate Limiting**: Groq and Google APIs have rate limits; exponential backoff handles this
3. **Image Count**: Maximum 5 images per VLM request (API limitation)
4. **Async/Sync Mixing**: Database operations are synchronous; async wrappers available but unused
5. **Error Recovery**: Failed tasks logged but orchestration continues with partial results

### 📈 Performance Metrics
- **Scraping Speed**: ~1 product per second (with AI enrichment)
- **LLM Response Time**: ~0.5-2 seconds per request
- **VLM Response Time**: ~2-5 seconds per request
- **Embedding Generation**: ~10-50ms per product
- **Database Queries**: Sub-millisecond for indexed lookups

---

## 🧪 Testing & Validation

### Evaluation Framework
- **Location**: `evals/` directory
- **Components**:
  - `run_eval.py`: Main evaluation runner with batch processing
  - `evaluators.py`: Comparison functions for different data types
  - `metrics.py`: Metrics calculation and export (CSV, JSON)
  - `schemas.py`: Schema definitions for ground truth data

### Evaluation Metrics
- **Exact Match**: For brand and string fields
- **Precision/Recall**: For list-based fields (allergens, attributes)
- **Subjective Scoring**: For price classification with equivalence mapping
- **Numeric Tolerance**: For nutritional values with relative error thresholds

### Test Files
- `tests/test_ai.py`: Tests `AIOrchestrator` with real product URLs
- `tests/test_scraper.py`: Tests `run_single_scrape()` for scraping validation
- `evals/run_eval.py`: Comprehensive evaluation against ground truth

### Data Validation
- Pydantic models validate LLM and VLM responses
- Type checking for database fields
- Schema enforcement at ingestion layer

---

## 🔐 Configuration & Setup

### Environment Setup
```bash
# Create virtual environment
python -m venv env_windows

# Activate environment
.\env_windows\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Database Setup
```bash
# For PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost/mercadona"

# For SQLite
export DATABASE_URL="sqlite:///./mercadona.db"

# Initialize database
python -m databases.db_operations.init_db()
```

### API Keys
Set the following in `.env`:
- `GROQ_API_KEY`: Groq API credentials
- `GOOGLE_API_KEY`: Google Gemini API credentials
- `DATABASE_URL`: Database connection string
- `COLLECTION_NAME`: Chroma collection name

---

## 📚 Project Structure

```
AI-Product-Recommender/
├── data/                           # 📁 Generated/downloaded data
│   ├── images/                     # Product images by ID
│   │   ├── 10502/
│   │   ├── 12562/
│   │   └── ... (26+ product folders)
│   ├── chroma_db/                  # Vector database persistence
│   ├── df_products.csv             # Exported product DataFrame
│   └── ground_truth_evals/         # Evaluation ground truth
│       └── product_info.csv        # Reference data for evaluation
│
├── backend/                        # 🔧 Backend services (old structure)
│   ├── app/
│   │   ├── test_llm.py
│   │   ├── user_prompt.py
│   │   └── prompts/
│   │       ├── LLM_decision.txt
│   │       └── LLM_SQL.txt
│
├── src/                            # 💻 New modular source code
│   ├── ai/                         # AI/LLM orchestration
│   │   ├── config.py               # Model provider configuration
│   │   ├── orchestrator.py         # AIOrchestrator class (main logic)
│   │   ├── prompts.py              # Prompt loading utilities
│   │   ├── schemas.py              # Pydantic models (RelativePrice, NutritionalInfo, Allergens)
│   │   ├── prompts/                # Prompt templates
│   │   │   ├── allergens_prompt.txt
│   │   │   ├── nutritional_info_prompt.txt
│   │   │   └── relative_price_prompt.txt
│   │   └── old_prompts/            # Legacy prompts
│   │
│   ├── database/                   # Database layer
│   │   ├── db_operations.py        # High-level DB operations
│   │   ├── db_utils.py             # SQLAlchemy setup, Product model
│   │   └── models.py               # (Currently empty)
│   │
│   └── scraper/                    # Web scraping
│       ├── playwright_scraper.py   # Main scraper orchestrator
│       ├── utils.py                # Scraping utilities
│       └── __pycache__/
│
├── evals/                          # 🧪 Evaluation framework
│   ├── run_eval.py                 # Main evaluation runner
│   ├── evaluators.py               # Comparison functions
│   ├── metrics.py                  # Metrics calculation
│   ├── schemas.py                  # Evaluation schemas
│   ├── try.ipynb                   # Development notebook
│   └── reports/                    # Evaluation results
│       ├── 2026-03-23_195845/
│       ├── 2026-03-23_200818/
│       └── ... (multiple timestamped reports)
│
├── scripts/                        # 🛠️ Utility scripts
│   ├── clear_relational.py         # Clear relational database
│   ├── clear_vector.py             # Clear vector database
│   └── run_scraper_pipeline.py     # Scraper orchestrator
│
├── scraping/                       # 📜 Legacy scraping code
│   ├── scraper_fast.py
│   ├── scraper.py
│   ├── utils.py
│   └── measurement.txt
│
├── tests/                          # 🧪 Test files
│   ├── test_ai.py                  # AIOrchestrator testing
│   ├── test_db_conn.py
│   ├── test_download_img.py
│   ├── test_rate_limiter.py
│   ├── test_scraper.py             # Scraper testing
│   ├── test_semaphore.py
│   └── __pycache__/
│
├── .venv/                          # Virtual environment
├── .gitignore
├── .env                            # (Not in git)
├── .env.example                    # Environment template
├── PROJECT_CONTEXT.md              # This file
├── README.md
├── TODO.txt
├── fixes.txt
├── pyproject.toml
├── project_structure.txt
└── VISUAL_OVERVIEW_EVALS.md
```

---

## 🎓 Key Concepts

### AIOrchestrator Class Pattern
The `AIOrchestrator` class encapsulates the AI pipeline:
- **Initialization**: Pre-builds all chains and models in `__init__()` to avoid re-initialization
- **Task Methods**: Each extraction task is a separate async method with retry logic
- **Orchestration**: `orchestrate_AI_pipeline()` runs all enabled tasks concurrently
- **Error Handling**: Returns exceptions as results; caller decides how to handle failures

### Dynamic Image Handling for VLMs
```python
# Build content with unpacked images
content = [{"type": "text", "text": "Extrae la información nutricional"}]
content.extend([{"type": "image_url", "image_url": {"url": url}} for url in urls])

# Build HumanMessage with content
messages = [
    SystemMessage(content=self.nutri_prompt),
    HumanMessage(content=content)  # Each image is a separate dict in the array
]
```
Key point: Images must be deserialized (unpacked with `*`) so each becomes a separate element, not a nested list.

### Semantic Search Strategy
- **Embeddings Model**: BAAI/bge-m3 (multilingual, 768-dimensional)
- **Storage**: Chroma vector database with persistent storage
- **Query Process**: Convert user query to embedding, find K nearest neighbors
- **Metadata**: Product ID stored with embedding for O(1) lookup

### Retry Logic with Tenacity
```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type(Exception)
)
```
- Exponential backoff: 2s, 4s, 8s, 16s, 32s, 60s
- Retries up to 5 times
- Logs attempt number and exception details

### Multi-Provider AI Setup
- **Price Classification**: Groq (llama-3.3-70b) - fast, cost-effective
- **Allergen Extraction**: Groq (moonshot/kimi-k2) - specialized for text
- **Nutritional Info**: Google Gemini (gemini-3.1-flash-lite) - best for vision tasks

---

## 🔮 Future Enhancements

### Short-term (Next Sprint)
1. **Async Database Operations**: Implement async SQLAlchemy for non-blocking DB calls
2. **Batch Processing**: Group products for parallel LLM/VLM requests
3. **Caching Layer**: Cache embeddings and frequent LLM responses
4. **Improved Error Recovery**: Implement DLQ (Dead Letter Queue) for failed products
5. **Verbose Output**: Add flag to display predicted vs ground truth data

### Medium-term (Q2 2026)
1. **User Preferences**: Personalize recommendations based on user history
2. **Price Tracking**: Monitor price changes over time
3. **Availability Alerts**: Notify users when products become available/unavailable
4. **Image Similarity**: Add visual similarity to semantic search
5. **Distributed Scraping**: Scale to handle multiple product catalogs

### Long-term (Q3-Q4 2026)
1. **Custom Fine-tuned Models**: Train domain-specific models for better extraction
2. **Cross-store Comparison**: Compare Mercadona with El Corte Inglés, Carrefour, etc.
3. **Mobile App**: React Native or Flutter for iOS/Android
4. **ML-based Ranking**: Learn from user interactions to improve recommendations
5. **Real-time Updates**: WebSocket support for live price/availability changes

---

## 📝 Notes & Observations

### Architecture Improvements Made
1. **Class-based Orchestration**: Moved from functional to OOP pattern for better state management
2. **LangChain Integration**: Standardized LLM/VLM calls through LangChain abstractions
3. **Provider Flexibility**: Easy switching between Groq, Google, and other providers
4. **Structured Output**: Pydantic models ensure type safety and validation
5. **Retry Resilience**: Tenacity decorators provide declarative retry logic

### Technical Debt Items
1. **No Database Migrations**: Manual schema updates; should use Alembic
2. **Hardcoded Constants**: `WAIT_TIME`, retry counts should be configurable
3. **Logging**: Using print statements; should migrate to logging module
4. **No Async DB Layer**: Database operations are synchronous (blocking)
5. **Evaluation Dependency**: eval depends on test_ai.py; should be decoupled

### Code Quality Recommendations
1. Implement structured logging (logging.getLogger)
2. Add comprehensive docstrings to all functions
3. Use dependency injection for better testability
4. Add type hints throughout the codebase
5. Create integration tests for end-to-end pipelines
6. Implement database migrations with Alembic

### Performance Optimization Opportunities
1. **Connection Pooling**: Increase DB pool size for concurrent writes
2. **Batch Embeddings**: Group products and generate embeddings in batches
3. **Image Compression**: Pre-compress images before VLM processing
4. **Query Caching**: Cache frequently accessed product queries
5. **Async I/O**: Convert blocking I/O operations to async where possible

---

## 🤝 Collaboration & Maintenance

### Code Quality
- Use pre-commit hooks for linting and formatting
- Follow PEP 8 style guidelines
- Document complex functions with docstrings
- Add type hints throughout the codebase

### Debugging Tips
1. Check `.env` for missing or incorrect API keys
2. Monitor Groq API rate limits in logs
3. Verify database connection strings
4. Inspect Pydantic validation errors for schema mismatches
5. Use screenshot functions in Playwright for scraping issues

---

## 📞 Support & Resources

### Key Files for Understanding the System
- `src/ai/orchestrator.py`: Core AI pipeline and task orchestration
- `src/scraper/playwright_scraper.py`: Web scraping implementation
- `src/database/db_utils.py`: Database schema and setup
- `src/ai/config.py`: Model provider configuration
- `evals/run_eval.py`: Evaluation framework

### API Documentation & References
- **LangChain**: https://python.langchain.com/docs/
- **Groq API**: https://console.groq.com/docs
- **Google Gemini**: https://ai.google.dev/docs
- **Chroma**: https://docs.trychroma.com
- **SQLAlchemy**: https://docs.sqlalchemy.org
- **Playwright**: https://playwright.dev/python
- **Tenacity**: https://tenacity.readthedocs.io/

### Common Commands
```bash
# Run scraper pipeline
python -m src.scraper.playwright_scraper

# Run AI tests
python tests/test_ai.py

# Run evaluation
python evals/run_eval.py --limit 5

# Clear databases
python scripts/clear_relational.py
python scripts/clear_vector.py

# Initialize database
python -m src.database.db_operations
```

### Debugging Tips
1. Check `.env` for missing or incorrect API keys
2. Monitor API rate limits in error messages
3. Enable verbose logging in LangChain: `langchain.debug = True`
4. Use Playwright screenshots for scraping issues: `await page.screenshot(path="debug.png")`
5. Check database logs for connection issues
6. Validate Pydantic models with: `model.model_validate_json(response_text)`

---

---

## 📋 Quick Reference: AIOrchestrator Usage

```python
from src.ai.orchestrator import AIOrchestrator

# Initialize orchestrator (pre-loads models and chains)
orchestrator = AIOrchestrator()

# Run full pipeline
result = await orchestrator.orchestrate_AI_pipeline(
    relative_price=True,
    nutritional_info=True,
    allergens=True,
    product_ID="22966",
    title="Cereal Copos de Maiz",
    price_description="250g",
    image_urls=["url1", "url2"],
    product_description="Sin azúcares añadidos..."
)

# Or run individual tasks
price = await orchestrator.extract_relative_price(title, price_desc)
nutrition = await orchestrator.extract_nutritional_info(image_urls)
allergens = await orchestrator.extract_allergens(product_desc)
```

### Expected Output
```json
{
  "precio_relativo": "estandar",
  "marca": "Hacendado",
  "atributos": ["sin gluten", "vegano"],
  "energia_kcal": 350,
  "grasas_g": 3.5,
  "carbohidratos_g": 85,
  "azucar_g": 1,
  "alergenos": ["trazas de frutos secos"]
}
```

---

**Last Updated**: March 30, 2026  
**Project Version**: 1.1 (Refactored with AIOrchestrator)  
**Status**: Fully Functional with Active Development  
**Main Contributor**: Gonzalo Martín
