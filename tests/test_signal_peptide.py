import pytest

from app.analysis.signal_peptide import predict_signal_peptide

# N-terminal sequences of proteins with well-characterised signal peptides.
# The cleavage position is the last residue of the signal peptide.
KNOWN_SIGNAL_PEPTIDES = {
    "E. coli OmpA": (
        "MKKTAIAIAVALAGFATVAQAAPKDNTWYTGAKLGWSQYHDTGFINNNGPT", 21,
    ),
    "human serum albumin": (
        "MKWVTFISLLFLFSSAYSRGVFRRDAHKSEVAHRFKDLGEENFKALVLIAFAQYLQQ", 18,
    ),
    "human preproinsulin": (
        "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKT", 24,
    ),
    "human growth hormone": (
        "MATGSRTSLLLAFGLLCLPWLQEGSAFPTIPLSRLFDNAMLRAHRLHQLAFDTYQEFEE", 26,
    ),
    "E. coli alkaline phosphatase": (
        "MKQSTIALALLPLLFTPVTKARTPEMPVLENRAAQGDITAPGGARRLTGDQTAALRDS", 21,
    ),
    "human lysozyme C": (
        "MKALIVLGLVLLSVTVQGKVFERCELARTLKRLGMDGYRGISLANWMCLAKWESGYNTRATNYNAG",
        18,
    ),
}

# Proteins without a signal peptide.
NEGATIVE_CONTROLS = {
    "GFP": (
        "MSKGEELFTGVVPILVELDGDVNGHKFSVSGEGEGDATYGKLTLKFICTTGKLPVPWPTLVTTFSYGV"
        "QCFSRYPDHMKQHDFFKSAMPEGYVQERTIFFKDDGNYKTRAEVKFEGDTLVNRIELKGIDFKEDGNI"
    ),
    "E. coli beta-galactosidase": (
        "MTMITDSLAVVLQRRDWENPGVTQLNRLAAHPPFASWRNSEEARTDRPSQQLRSLNGEWRFAWFPAPE"
        "AVPESWLECDLPEADTVVVPSNWQ"
    ),
    "ubiquitin": (
        "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLH"
        "LVLRLRGG"
    ),
    "beta-actin": (
        "MDDDIAALVVDNGSGMCKAGFAGDDAPRAVFPSIVGRPRHQGVMVGMGQKDSYVGDEAQSKRGILTLK"
        "YPIEHGIITNWDDMEKIWHHTFYNELRVAPEEHPTLLTEAPLNPKANREKMTQIMFETFNVPAMYVAI"
    ),
}


@pytest.mark.parametrize("name", KNOWN_SIGNAL_PEPTIDES)
def test_known_signal_peptides_are_detected(name):
    sequence, _cleavage = KNOWN_SIGNAL_PEPTIDES[name]

    result = predict_signal_peptide(sequence)

    assert result["detected"] is True, name
    assert result["confidence"] in {"low", "medium"}


@pytest.mark.parametrize("name", KNOWN_SIGNAL_PEPTIDES)
def test_cleavage_estimate_is_close_to_the_known_site(name):
    sequence, cleavage = KNOWN_SIGNAL_PEPTIDES[name]

    result = predict_signal_peptide(sequence)

    assert abs(result["cleavage_after"] - cleavage) <= 2, name


@pytest.mark.parametrize("name", NEGATIVE_CONTROLS)
def test_proteins_without_signal_peptides_are_not_detected(name):
    result = predict_signal_peptide(NEGATIVE_CONTROLS[name])

    assert result["detected"] is False, name
    assert result["reasons"]
    assert result["cleavage_after"] is None


def test_result_describes_the_three_regions():
    sequence, _ = KNOWN_SIGNAL_PEPTIDES["human serum albumin"]

    result = predict_signal_peptide(sequence)

    n_region, h_region, c_region = (
        result["n_region"], result["h_region"], result["c_region"]
    )

    assert n_region["start"] == 1
    assert n_region["end"] < h_region["start"]
    assert h_region["end"] < c_region["start"]
    assert c_region["end"] == result["cleavage_after"]
    assert n_region["net_charge"] >= 0
    assert h_region["mean_hydropathy"] >= 2.0
    assert len(result["cleavage_motif"]) == 3


def test_cleavage_motif_follows_the_minus_three_minus_one_rule():
    for sequence, _ in KNOWN_SIGNAL_PEPTIDES.values():
        motif = predict_signal_peptide(sequence)["cleavage_motif"]

        assert motif[0] in "ASGVILTC"
        assert motif[2] in "AGSCT"


def test_short_sequences_are_not_screened():
    result = predict_signal_peptide("MKKTAIAIAVALAGFATVAQA")

    assert result["detected"] is False
    assert "shorter" in result["reasons"][0]


def test_negative_n_region_charge_is_reported_as_a_reason():
    result = predict_signal_peptide(NEGATIVE_CONTROLS["GFP"])

    assert any("negative" in reason for reason in result["reasons"])


def test_invalid_sequences_are_rejected():
    with pytest.raises(ValueError):
        predict_signal_peptide("MKKTAIAIAVALAGFATVAQAAPKDNTWYTGAK!")


def test_result_states_it_is_a_heuristic():
    sequence, _ = KNOWN_SIGNAL_PEPTIDES["E. coli OmpA"]

    result = predict_signal_peptide(sequence)

    assert "heuristic" in result["method"].lower()
    assert any("SignalP" in note for note in result["notes"])
