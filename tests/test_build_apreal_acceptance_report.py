from docx import Document
from docx.oxml.ns import qn

from tools.build_apreal_acceptance_report import set_table_width


def test_set_table_width_persists_exact_grid_for_new_rows():
    document = Document()
    table = document.add_table(rows=1, cols=3)

    set_table_width(table, [0.5, 1.5, 4.5])
    new_row = table.add_row()

    table_width = table._tbl.tblPr.find(qn("w:tblW"))
    table_indent = table._tbl.tblPr.find(qn("w:tblInd"))
    grid_widths = [int(column.get(qn("w:w"))) for column in table._tbl.tblGrid]
    cell_widths = [
        int(cell._tc.get_or_add_tcPr().find(qn("w:tcW")).get(qn("w:w")))
        for cell in new_row.cells
    ]

    assert table_width.get(qn("w:type")) == "dxa"
    assert int(table_width.get(qn("w:w"))) == 9360
    assert table_indent.get(qn("w:type")) == "dxa"
    assert int(table_indent.get(qn("w:w"))) == 120
    assert grid_widths == [720, 2160, 6480]
    assert cell_widths == grid_widths
