from blueprints import main_bp, sub_blueprint
import os


def generate():
    print("🎨 Generating blueprint graphs...")
    main_bp.render_graph("full_showcase_graph")
    sub_blueprint.render_graph("metadata_enrichment_graph")
    print(f"✅ Done. Check {os.getcwd()} for .png files.")


if __name__ == "__main__":
    generate()
