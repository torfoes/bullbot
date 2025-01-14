# bullbot
Open source trading bot that captures ETH & L2 volatility with, on-chain swaps, and sentiment analysis.

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   
2. **Install dependencies:**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up .env file with SECRET_KEY, DEBUG, and other environment variables.**
4. **Apply migrations**
    ```bash
    python manage.py migrate
    ```

5. **Run the development server:**
    ```bash
   python manage.py runserver
    ```