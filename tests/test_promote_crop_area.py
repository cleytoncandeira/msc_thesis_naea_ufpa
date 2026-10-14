import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from promote_crop_area import main


def test_crop_promotion_script_writes_outputs(tmp_path):
    consensus = tmp_path / "consensus.csv"
    review = tmp_path / "review.csv"
    output = tmp_path / "output"
    consensus.write_text(
        "document_id,document_path,field_name,selected_value_raw,selected_value_numeric,candidate_values,candidate_pages,candidate_count,consensus_status,review_excerpt\n"
        "doc,doc.pdf,certified_soy_area_ha,100,100,100,3,1,single_direct_crop_area_candidate,evidence\n",
        encoding="utf-8",
    )
    review.write_text(
        "document_id,document_path,field_name,selected_value_raw,selected_value_numeric,candidate_values,candidate_pages,candidate_count,consensus_status,review_excerpt,human_decision,corrected_value,reviewer,review_notes\n"
        "doc,doc.pdf,certified_soy_area_ha,100,100,100,3,1,single_direct_crop_area_candidate,evidence,accept,,,\n",
        encoding="utf-8",
    )
    assert main(["--consensus", str(consensus), "--review", str(review), "--output-dir", str(output)]) == 0
    assert (output / "crop_area_promoted.csv").exists()
