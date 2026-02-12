SET TERM ^ ;

CREATE OR ALTER PROCEDURE CORRIGE_SEQUENCIA_BPI 
returns (
    prd_uid varchar(7),
    prd_cmp varchar(6),
    prd_pa varchar(10),
    prd_cnsmed varchar(15),
    prd_cbo varchar(6),
    prd_flh varchar(3),
    prd_seq varchar(2),
    prd_idade varchar(3),
    prd_qt_p double precision,
    prd_org varchar(3),
    prd_flh_novo varchar(3),
    prd_seq_novo varchar(2),
    prd_nmpac varchar(30),
    prd_dtaten varchar(8),
    prd_dtnasc varchar(8))
as
declare variable fol_novo integer = 0;
declare variable seq_novo integer = 0;
declare variable prev_cnsmed varchar(15) = '';
declare variable prev_cmp varchar(6) = '';
BEGIN
    fol_novo = 0;
    seq_novo = 0;
    prev_cnsmed = '';
    prev_cmp = '';

    FOR
    SELECT
        prd_uid, prd_cmp, prd_pa, prd_cnsmed, prd_cbo,
        prd_flh, prd_seq, prd_idade, prd_qt_p,
        prd_org, prd_nmpac, prd_dtnasc, prd_dtaten
    FROM s_prd
    WHERE prd_org = 'BPI'
    ORDER BY prd_cmp, prd_cnsmed, prd_pa, prd_dtaten, prd_uid
    INTO
        :prd_uid, :prd_cmp, :prd_pa, :prd_cnsmed, :prd_cbo,
        :prd_flh, :prd_seq, :prd_idade, :prd_qt_p,
        :prd_org, :prd_nmpac, :prd_dtnasc, :prd_dtaten
    DO
    BEGIN
        seq_novo = seq_novo + 1;

    IF (:prd_cnsmed <> :prev_cnsmed) THEN
    BEGIN
        prev_cnsmed = :prd_cnsmed;
        seq_novo = 1;
        fol_novo = 1;
    END

    IF (:prd_cmp <> :prev_cmp) THEN
    BEGIN
        prev_cmp = :prd_cmp;
        seq_novo = 1;
        fol_novo = 1;
    END

    IF (seq_novo > 99) THEN
    BEGIN
        seq_novo = 1;
        fol_novo = fol_novo + 1;
    END

    prd_flh_novo = SM_PADLEFT(CAST(fol_novo AS VARCHAR(3)), '0', 3);
    prd_seq_novo = SM_PADLEFT(CAST(seq_novo AS VARCHAR(2)), '0', 2);

    UPDATE s_prd
    SET prd_flh = :prd_flh_novo,
    prd_seq = :prd_seq_novo
        WHERE prd_uid = :prd_uid
        AND prd_cmp = :prd_cmp
        AND prd_pa = :prd_pa
        AND prd_cnsmed = :prd_cnsmed
        AND prd_cbo = :prd_cbo
        AND prd_flh = :prd_flh
        AND prd_seq = :prd_seq
        AND prd_idade = :prd_idade
        AND prd_qt_p = :prd_qt_p
        AND prd_org = :prd_org
        AND prd_nmpac = :prd_nmpac
        AND prd_dtnasc = :prd_dtnasc
        AND prd_dtaten = :prd_dtaten;

    SUSPEND;
    END
END^

SET TERM ; ^