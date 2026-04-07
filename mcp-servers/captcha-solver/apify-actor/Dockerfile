# Build context: captcha-solver/ root (set via dockerContextDir in actor.json)
FROM apify/actor-python:3.12

# Install solver dependencies (VLM-only, no torch/CLIP)
COPY --chown=myuser:myuser apify-actor/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy captcha-solver core library
COPY --chown=myuser:myuser core/ ./captcha-solver/core/
COPY --chown=myuser:myuser router.py ./captcha-solver/
COPY --chown=myuser:myuser vision/ ./captcha-solver/vision/
COPY --chown=myuser:myuser solvers/ ./captcha-solver/solvers/

# Copy Actor source
COPY --chown=myuser:myuser apify-actor/src/ ./src/
COPY --chown=myuser:myuser apify-actor/.actor/ ./.actor/

CMD python3 -m src
