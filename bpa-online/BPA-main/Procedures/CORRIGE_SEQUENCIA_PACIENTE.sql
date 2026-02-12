SET TERM ^ ;

CREATE OR ALTER PROCEDURE CORRIGE_SEQUENCIA_PACIENTE
returns (
    prd_uid varchar(7),
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
declare variable fol_novo integer;
declare variable seq_novo integer;
begin
    fol_novo = 1;
    seq_novo = 0;

    for select
        s_prd.prd_uid,
        s_prd.prd_pa,
        s_prd.prd_cnsmed,
        s_prd.prd_cbo,
        s_prd.prd_flh,
        s_prd.prd_seq,
        s_prd.prd_idade,
        s_prd.prd_qt_p,
        s_prd.prd_org,
        s_prd.prd_nmpac,
        s_prd.prd_dtnasc,
        s_prd.prd_dtaten
    from s_prd
    where s_prd.prd_org = 'BPI'
    order by s_prd.prd_nmpac, s_prd.prd_uid, s_prd.prd_pa
    into :prd_uid, :prd_pa, :prd_cnsmed, :prd_cbo, :prd_flh, :prd_seq, :prd_idade, :prd_qt_p, :prd_org, :prd_nmpac, :prd_dtnasc, :prd_dtaten
    do begin

        seq_novo = :seq_novo + 1;

        -- Se a sequência exceder 99, reinicia e incrementa a folha
        if (:seq_novo > 99) then
        begin
            seq_novo = 1;
            fol_novo = :fol_novo + 1;
        end

        prd_flh_novo = SM_PADLEFT(cast(:fol_novo as varchar(3)),'0',3);
        prd_seq_novo = SM_PADLEFT(cast(:seq_novo as varchar(2)),'0',2);

        update s_prd set s_prd.prd_flh = :prd_flh_novo, s_prd.prd_seq = :prd_seq_novo
        where s_prd.prd_uid = :prd_uid
        and s_prd.prd_pa = :prd_pa
        and s_prd.prd_cnsmed = :prd_cnsmed
        and s_prd.prd_cbo = :prd_cbo
        and s_prd.prd_flh = :prd_flh
        and s_prd.prd_seq = :prd_seq
        and s_prd.prd_idade = :prd_idade
        and s_prd.prd_qt_p = :prd_qt_p
        and s_prd.prd_org = :prd_org
        and s_prd.prd_nmpac = :prd_nmpac
        and s_prd.prd_dtnasc = :prd_dtnasc
        and s_prd.prd_dtaten = :prd_dtaten;

        suspend;
    end
end^

SET TERM ; ^
