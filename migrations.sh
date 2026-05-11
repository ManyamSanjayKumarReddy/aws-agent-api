#!/bin/bash
# =============================================================================
# AWS Agent — Aerich Migration Runbook
# =============================================================================
# Prerequisites:
#   - Never mount migrations/ as a Docker volume
#   - After any aerich command inside the container, sync back to local:
#       docker compose cp app:/app/migrations ./migrations
#   - Never run init-db on prod unless the DB is completely empty
# =============================================================================

set -e

DB_SERVICE="postgres"
APP_SERVICE="app"
DB_USER="awsagent"
DB_NAME="awsagent_db"
TORTOISE_ORM="app.core.database.TORTOISE_ORM_CONFIG"

# -----------------------------------------------------------------------------
# SECTION 1 — First Time Setup (fresh DB, no tables)
# -----------------------------------------------------------------------------
fresh_setup() {
    echo "==> [Fresh Setup] Wiping containers and DB volume..."
    docker compose down -v

    echo "==> Deleting local migrations folder..."
    rm -rf migrations/

    echo "==> Building and starting containers..."
    docker compose up --build -d

    echo "==> Waiting for DB to be ready..."
    sleep 5

    echo "==> Initialising aerich..."
    docker compose exec $APP_SERVICE uv run aerich init -t $TORTOISE_ORM

    echo "==> Creating all tables..."
    docker compose exec $APP_SERVICE uv run aerich init-db

    echo "==> Verifying tables..."
    docker compose exec $DB_SERVICE psql -U $DB_USER -d $DB_NAME -c "\dt"

    echo "==> Syncing migration files back to local..."
    docker compose cp $APP_SERVICE:/app/migrations ./migrations

    echo "==> Fresh setup complete."
}

# -----------------------------------------------------------------------------
# SECTION 2 — After Every Model Change
# -----------------------------------------------------------------------------
# Usage: ./migrations.sh migrate <describe_change>
# Example: ./migrations.sh migrate add_message_metadata
# -----------------------------------------------------------------------------
migrate() {
    NAME=$1
    if [ -z "$NAME" ]; then
        echo "ERROR: Provide a migration name. Usage: ./migrations.sh migrate <name>"
        exit 1
    fi

    echo "==> [Model Change] Rebuilding containers..."
    docker compose up --build -d

    echo "==> Generating migration: $NAME..."
    docker compose exec $APP_SERVICE uv run aerich migrate --name $NAME

    echo "==> Applying migration..."
    docker compose exec $APP_SERVICE uv run aerich upgrade

    echo "==> Syncing migration files back to local..."
    docker compose cp $APP_SERVICE:/app/migrations ./migrations

    echo "==> Migration '$NAME' applied."
}

# -----------------------------------------------------------------------------
# SECTION 3 — After Git Pull on Prod (existing DB, new migrations from repo)
# -----------------------------------------------------------------------------
prod_deploy() {
    echo "==> [Prod Deploy] Rebuilding containers..."
    docker compose up --build -d

    echo "==> Applying pending migrations (upgrade only — no init or init-db on prod)..."
    docker compose exec $APP_SERVICE uv run aerich upgrade

    echo "==> Deploy complete."
}

# -----------------------------------------------------------------------------
# SECTION 4 — Full Local Reset
# -----------------------------------------------------------------------------
reset_local() {
    echo "==> [Local Reset] Wiping containers and DB volume..."
    docker compose down -v

    echo "==> Deleting local migrations folder..."
    rm -rf migrations/

    echo "==> Rebuilding containers..."
    docker compose up --build -d

    echo "==> Waiting for DB to be ready..."
    sleep 5

    echo "==> Initialising aerich..."
    docker compose exec $APP_SERVICE uv run aerich init -t $TORTOISE_ORM

    echo "==> Creating tables..."
    docker compose exec $APP_SERVICE uv run aerich init-db

    echo "==> Verifying tables..."
    docker compose exec $DB_SERVICE psql -U $DB_USER -d $DB_NAME -c "\dt"

    echo "==> Syncing migration files back to local..."
    docker compose cp $APP_SERVICE:/app/migrations ./migrations

    echo "==> Local reset complete."
}

# -----------------------------------------------------------------------------
# SECTION 5 — Full Prod Reset (DANGEROUS — only if DB is intentionally wiped)
# -----------------------------------------------------------------------------
reset_prod() {
    echo "==> [Prod Reset] WARNING: This will wipe the entire DB schema."
    read -p "Are you sure? Type 'yes' to continue: " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi

    echo "==> Dropping and recreating public schema..."
    docker compose exec $DB_SERVICE psql -U $DB_USER -d $DB_NAME \
        -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

    echo "==> Rebuilding containers..."
    docker compose up --build -d

    echo "==> Waiting for DB to be ready..."
    sleep 5

    echo "==> Initialising aerich..."
    docker compose exec $APP_SERVICE uv run aerich init -t $TORTOISE_ORM

    echo "==> Creating tables..."
    docker compose exec $APP_SERVICE uv run aerich init-db

    echo "==> Prod reset complete."
}

# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------
case "$1" in
    fresh)        fresh_setup ;;
    migrate)      migrate "$2" ;;
    deploy)       prod_deploy ;;
    reset-local)  reset_local ;;
    reset-prod)   reset_prod ;;
    *)
        echo ""
        echo "Usage: ./migrations.sh <command> [args]"
        echo ""
        echo "Commands:"
        echo "  fresh                    First time setup — wipe, build, init-db, sync"
        echo "  migrate <name>           After model change — build, migrate, upgrade, sync"
        echo "  deploy                   After git pull on prod — build, upgrade only"
        echo "  reset-local              Full local reset — wipe everything and reinit"
        echo "  reset-prod               Full prod reset (DANGEROUS) — drop schema and reinit"
        echo ""
        echo "Examples:"
        echo "  ./migrations.sh fresh"
        echo "  ./migrations.sh migrate add_message_metadata"
        echo "  ./migrations.sh deploy"
        echo ""
        ;;
esac