# Master EDA: AI Agent for Charts & Insights

A full-stack AI-powered Exploratory Data Analysis (EDA) web application that automatically generates visualizations and provides intelligent insights using Google Gemini 2.0 Flash.

## 🚀 Features

- **Automatic CSV Upload & Processing**: Upload CSV files and get instant analysis
- **Smart Data Cleaning**: Automatic handling of missing values, type inference, and outlier detection
- **Rich Visualizations**: Auto-generated charts including:
  - Histograms
  - Box plots
  - Correlation heatmaps
  - Pair plots
  - Distribution plots
  - Missing value matrices
  - Bar charts for categorical data
- **AI-Powered Insights**: Get intelligent analysis from Google Gemini 2.0 Flash
- **Beautiful Dashboard**: Modern, responsive UI with interactive charts
- **Statistical Analysis**: Comprehensive summary statistics and data quality checks

## 🛠️ Tech Stack

### Backend
- **Framework**: Django REST Framework
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Matplotlib, Seaborn
- **AI Model**: Google Gemini 2.0 Flash API
- **Database**: SQLite (can be upgraded to PostgreSQL)

### Frontend
- **Framework**: React 18 with Vite
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Styling**: Custom CSS with CSS Variables

## 📋 Prerequisites

- Python 3.12+
- Node.js 16+
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

## 🔧 Installation

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the backend directory:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   SECRET_KEY=your_django_secret_key_here
   DEBUG=True
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

7. **Start the development server**:
   ```bash
   python manage.py runserver
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

The frontend will be available at `http://localhost:3000`

## 🎯 Usage

1. **Open the application** in your browser at `http://localhost:3000`

2. **Upload a CSV file** by dragging and dropping or clicking to select

3. **View automatic visualizations** on the dashboard

4. **Generate AI insights** by clicking the "Generate AI Insights" button

5. **Download charts** using the download button on each chart

## 📁 Project Structure

```
eda-analyzer/
├── backend/
│   ├── config/                 # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── eda/                    # Main Django app
│   │   ├── models.py          # Database models
│   │   ├── views.py           # API views
│   │   ├── serializers.py     # DRF serializers
│   │   ├── urls.py            # App URLs
│   │   └── services/          # Business logic
│   │       ├── data_processor.py
│   │       ├── chart_generator.py
│   │       └── ai_insights.py
│   ├── media/                 # Uploaded files
│   ├── eda_outputs/           # Generated charts
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── Header.jsx
│   │   │   └── FileUpload.jsx
│   │   ├── pages/            # Page components
│   │   │   ├── Home.jsx
│   │   │   └── Dashboard.jsx
│   │   ├── utils/            # Utilities
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 🔌 API Endpoints

- `POST /api/upload_csv/` - Upload CSV file and initiate analysis
- `GET /api/eda_charts/<session_id>/` - Get all charts for a session
- `GET /api/ai_insights/<session_id>/` - Generate and retrieve AI insights
- `GET /api/sessions/` - List all sessions
- `GET /api/sessions/<session_id>/` - Get session details

## 🎨 Key Features Explained

### Data Processing
- Automatic column name normalization
- Intelligent type inference
- Missing value handling (median for numeric, mode for categorical)
- Outlier detection using IQR method

### Chart Generation
- Generates multiple chart types automatically
- Limits data points for performance optimization
- Saves charts as PNG images
- Provides download functionality

### AI Insights
- Uses Google Gemini 2.0 Flash for analysis
- Sends chart images and data summary
- Provides comprehensive insights including:
  - Data quality assessment
  - Statistical insights
  - Relationship analysis
  - Distribution patterns
  - Actionable recommendations

## 🚀 Deployment

### Backend Deployment (Railway/Render/Heroku)

1. Update `settings.py` for production:
   - Set `DEBUG = False`
   - Configure `ALLOWED_HOSTS`
   - Set up PostgreSQL database
   - Configure static files

2. Add production dependencies to `requirements.txt`:
   ```
   gunicorn
   psycopg2-binary
   whitenoise
   ```

3. Create `Procfile`:
   ```
   web: gunicorn config.wsgi
   ```

### Frontend Deployment (Vercel/Netlify)

1. Build the frontend:
   ```bash
   npm run build
   ```

2. Update API base URL in `src/utils/api.js` to point to production backend

3. Deploy the `dist` folder

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Google Gemini API for AI-powered insights
- Django REST Framework for the robust backend
- React and Vite for the modern frontend
- Matplotlib and Seaborn for beautiful visualizations

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using Django, React, and AI**
