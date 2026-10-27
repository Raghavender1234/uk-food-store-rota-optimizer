# Contributing to AI Rota & Shift Optimization Engine

We welcome contributions from developers, restaurant managers, operations researchers, and open-source enthusiasts!

---

## 💡 Ways to Contribute

1. **Add Solver Constraints**: Improve [dynamic_solver.py](file:///dynamic_solver.py) (e.g. night-shift turnaround rules, split-shifts, overtime penalty curves).
2. **Expand the NLP Parser**: Add new natural language patterns in [chat_parser.py](file:///chat_parser.py).
3. **Integrations**: Build connectors for weather APIs (OpenWeatherMap for rain spikes), POS systems (Toast, Square), or messaging (WhatsApp, Telegram).
4. **UI & Android Enhancements**: Improve the PWA UI or Kotlin Jetpack Compose companion app.

---

## 🛠️ Development Setup

1. Fork the repository and clone your fork.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run tests before submitting changes:
   ```bash
   python tests/test_diag.py
   python tests/test_universal.py
   ```
4. Start local development server:
   ```bash
   python app.py
   ```

---

## 📜 Pull Request Guidelines

- Ensure `tests/test_diag.py` passes without errors.
- Never commit real employee names or private wages in test files.
- Keep commits descriptive (`feat: ...`, `fix: ...`, `docs: ...`).
