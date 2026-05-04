from sqlalchemy import Column, String, Integer, Text, Boolean, TIMESTAMP, ForeignKey, Index, DECIMAL, Date, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = Column(String(255), unique=True, nullable=False, index=True)
    pdf_url = Column(Text, nullable=False)
    pdf_filename = Column(String(500))
    chunks_count = Column(Integer, nullable=False, default=0)
    embedding_model = Column(String(100), default='BAAI/bge-large-en')
    vectorstore_path = Column(Text)
    status = Column(String(50), default='active', index=True)
    doc_metadata = Column(JSONB)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    queries = relationship("Query", back_populates="document", cascade="all, delete-orphan")
    batch_jobs = relationship("BatchJob", back_populates="document", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_documents_created_at', 'created_at'),
    )


class Query(Base):
    __tablename__ = 'queries'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    query_text = Column(Text, nullable=False)
    refined_query = Column(Text)
    answer = Column(Text)
    final_answer = Column(Text)
    iteration_count = Column(Integer, default=0)
    max_iterations = Column(Integer, default=3)
    is_answer_correct = Column(Boolean, default=False, index=True)
    is_sufficient = Column(Boolean, default=False)
    
    retrieval_metadata = Column(JSONB)
    answer_metadata = Column(JSONB)
    evaluation_metadata = Column(JSONB)
    
    total_tokens = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_tokens = Column(Integer, default=0)
    estimated_cost = Column(DECIMAL(10, 6), default=0.0)
    
    processing_time_ms = Column(Integer)
    created_at = Column(TIMESTAMP, default=func.now(), index=True)
    completed_at = Column(TIMESTAMP)
    
    document = relationship("Document", back_populates="queries")
    agent_runs = relationship("AgentRun", back_populates="query", cascade="all, delete-orphan")


class BatchJob(Base):
    __tablename__ = 'batch_jobs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(String(50), nullable=False, default='pending', index=True)
    progress = Column(String(255))
    total_questions = Column(Integer, nullable=False, default=5)
    completed_questions = Column(Integer, default=0)
    error_message = Column(Text)
    
    created_at = Column(TIMESTAMP, default=func.now(), index=True)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    processing_time_ms = Column(Integer)
    
    document = relationship("Document", back_populates="batch_jobs")
    questions = relationship("BatchQuestion", back_populates="batch_job", cascade="all, delete-orphan")


class BatchQuestion(Base):
    __tablename__ = 'batch_questions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_job_id = Column(UUID(as_uuid=True), ForeignKey('batch_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    answer = Column(Text)
    iteration_count = Column(Integer, default=0)
    status = Column(String(50), default='pending')
    error_message = Column(Text)
    
    is_grounded = Column(Boolean)
    is_insightful = Column(Boolean)
    is_useful = Column(Boolean)
    has_hallucination = Column(Boolean)
    coverage = Column(String(20))
    
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(DECIMAL(10, 6), default=0.0)
    
    created_at = Column(TIMESTAMP, default=func.now())
    completed_at = Column(TIMESTAMP)
    
    batch_job = relationship("BatchJob", back_populates="questions")
    agent_runs = relationship("AgentRun", back_populates="batch_question", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_batch_questions_job_index', 'batch_job_id', 'question_index', unique=True),
    )


class AgentRun(Base):
    __tablename__ = 'agent_runs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey('queries.id', ondelete='CASCADE'), index=True)
    batch_question_id = Column(UUID(as_uuid=True), ForeignKey('batch_questions.id', ondelete='CASCADE'), index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    iteration = Column(Integer, nullable=False, default=0)
    
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    
    execution_time_ms = Column(Integer)
    tokens_used = Column(Integer, default=0)
    cost = Column(DECIMAL(10, 6), default=0.0)
    
    status = Column(String(50), default='success')
    error_message = Column(Text)
    
    created_at = Column(TIMESTAMP, default=func.now(), index=True)
    
    query = relationship("Query", back_populates="agent_runs")
    batch_question = relationship("BatchQuestion", back_populates="agent_runs")


class CostTracking(Base):
    __tablename__ = 'cost_tracking'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, index=True)
    agent_type = Column(String(50), index=True)
    model_name = Column(String(100))
    
    total_runs = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_tokens = Column(Integer, default=0)
    total_cost = Column(DECIMAL(10, 6), default=0.0)
    
    avg_tokens_per_run = Column(DECIMAL(10, 2))
    avg_cost_per_run = Column(DECIMAL(10, 6))
    
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_cost_tracking_unique', 'date', 'agent_type', 'model_name', unique=True),
    )


class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_name = Column(String(255), nullable=False)
    ticker = Column(String(50), nullable=False, index=True)
    screener_link = Column(String(500))
    market_size = Column(String(50))
    last_stock_price = Column(Integer)
    created_at = Column(TIMESTAMP, default=func.now())
    update_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    scrape_data = relationship("StockScrapeData", back_populates="stock", cascade="all, delete-orphan")
    transcripts = relationship("ConcallTranscript", back_populates="stock", cascade="all, delete-orphan")
    summaries = relationship("ConcallSummary", back_populates="stock", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_stocks_ticker', 'ticker'),
        Index('idx_stocks_created_at', 'created_at'),
    )


class StockScrapeData(Base):
    __tablename__ = 'stock_scrape_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    stockId = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'), index=True)
    quarter_result = Column(JSONB)
    growth_sales = Column(JSONB)
    growth_net_profit = Column(JSONB)
    growth_operating_profit = Column(JSONB)
    shareholding_pattern = Column(JSONB)
    profit_loss = Column(JSONB)
    quarter_date = Column(Date)
    
    stock = relationship("Stock", back_populates="scrape_data")
    
    __table_args__ = (
        Index('Stock_scrape_Data_stockId_idx', 'stockId'),
    )


class ConcallSummary(Base):
    __tablename__ = 'concall_summary'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    stockid = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    answer1 = Column(Text)
    answer2 = Column(Text)
    answer3 = Column(Text)
    answer4 = Column(Text)
    answer5 = Column(Text)
    prev_concall_hisotry = Column(Text)
    concall_url = Column(String)
    quarter_date = Column(Date)
    document_id = Column(String)
    
    stock = relationship("Stock", back_populates="summaries")
    transcript = relationship("ConcallTranscript", back_populates="summary", uselist=False)
    
    __table_args__ = (
        Index('concall_summary_stockid_idx', 'stockid'),
    )


class ConcallTranscript(Base):
    __tablename__ = 'concall_transcript'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, default=func.now())
    transcript_url = Column(String)
    quarter_date = Column(Date)
    status = Column(String)
    summary_id = Column(Integer, ForeignKey('concall_summary.id', ondelete='SET NULL'))
    stock_id = Column(Integer, ForeignKey('stocks.id', ondelete='CASCADE'))
    
    stock = relationship("Stock", back_populates="transcripts")
    summary = relationship("ConcallSummary", back_populates="transcript", foreign_keys=[summary_id])
    
    __table_args__ = ()