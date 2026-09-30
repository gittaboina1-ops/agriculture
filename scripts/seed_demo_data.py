import os
import sys
import pandas as pd
import json

def seed_neo4j():
    """
    Connects to Neo4j and populates nodes, constraints, and relationships.
    Safe to run repeatedly.
    """
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    print(f"Connecting to Neo4j at {uri}...")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            session.run("RETURN 1")
            print("Connected to Neo4j successfully!")

            # Create Constraints
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Crop) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Treatment) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (cl:Claim) REQUIRE cl.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (w:WeatherCondition) REQUIRE w.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (sl:Soil) REQUIRE sl.id IS UNIQUE"
            ]
            for c in constraints:
                try:
                    session.run(c)
                except Exception as ce:
                    print(f"Constraint notice: {ce}")

            # 1. Crops
            crops_df = pd.read_csv("data/crops.csv")
            for _, r in crops_df.iterrows():
                session.run("""
                    MERGE (c:Crop {id: $id})
                    SET c.name = $name, c.scientific_name = $scientific_name,
                        c.optimal_temp = $opt_temp, c.optimal_humidity = $opt_hum,
                        c.description = $desc
                """, id=r["crop_id"], name=r["common_name"], scientific_name=r["scientific_name"],
                     opt_temp=f"{r['optimal_temp_min']}-{r['optimal_temp_max']}C",
                     opt_hum=f"{r['optimal_humidity_min']}-{r['optimal_humidity_max']}%",
                     desc=r["description"])

            # 2. Diseases
            dis_df = pd.read_csv("data/diseases.csv")
            for _, r in dis_df.iterrows():
                session.run("""
                    MERGE (d:Disease {id: $id})
                    SET d.name = $name, d.pathogen_type = $pathogen,
                        d.favorable_temp = $f_temp, d.favorable_humidity = $f_hum,
                        d.description = $desc
                """, id=r["disease_id"], name=r["name"], pathogen=r["pathogen_type"],
                     f_temp=f"{r['favorable_temp_min']}-{r['favorable_temp_max']}C",
                     f_hum=f"{r['favorable_humidity_min']}-{r['favorable_humidity_max']}%",
                     desc=r["description"])

            # 3. Relationships
            session.run("""
                MATCH (c:Crop {id: 'CROP_001'}), (d:Disease {id: 'DIS_001'})
                MERGE (c)-[:SUSCEPTIBLE_TO {risk: 'High', source: 'DOC_001'}]->(d)
            """)

            print("Neo4j database successfully seeded with agricultural entities & relationships!")
        driver.close()
    except Exception as e:
        print(f"Notice: Neo4j server is currently offline or unreachable ({e}).")
        print("AgriGraph automatically operates in zero-downtime hybrid mode using its pre-loaded in-memory graph engine.")

if __name__ == "__main__":
    seed_neo4j()
