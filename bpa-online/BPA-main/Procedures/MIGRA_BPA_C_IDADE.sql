SET TERM ^ ;

CREATE OR ALTER PROCEDURE MIGRA_BPA_C_IDADE 
returns (
    prd_uid varchar(7),
    prd_pa varchar(10),
    prd_cbo varchar(6),
    prd_cmp varchar(6),
    prd_idade varchar(3),
    prd_qt_p double precision)
as
declare variable prd_pa_v varchar(10);
declare variable tp_bpa_v smallint;
begin
    for select s_prd.prd_uid,
               s_prd.prd_pa,
               s_prd.prd_cbo,
               s_prd.prd_cmp,
               s_prd.prd_idade,
               sum(s_prd.prd_qt_p)
        from s_prd
        where s_prd.prd_org = 'BPI'
          and s_prd.prd_pa in ('0301010110','0301010030','0301010048','0301010072','0301010056','0301010064','0301010137')
        group by 1,2,3,4,5
        into :prd_uid, :prd_pa, :prd_cbo, :prd_cmp, :prd_idade, :prd_qt_p
    do begin

   INSERT INTO s_prd (PRD_UID, PRD_CMP, PRD_CNSMED, PRD_CBO, PRD_FLH, PRD_SEQ, PRD_PA, PRD_CNSPAC, PRD_SEXO, PRD_IBGE, PRD_DTATEN, PRD_CID, PRD_IDADE, PRD_QT_P, PRD_CATEN, PRD_NAUT, PRD_ORG, PRD_MVM, PRD_FLPA, PRD_FLCBO, PRD_FLCA, PRD_FLIDA, PRD_FLQT, PRD_FLER, PRD_FLMUN, PRD_FLCID) VALUES (:prd_uid, :prd_cmp, '', :prd_cbo, '001', '01', :prd_pa, '', '', '', '', '', :prd_idade, :prd_qt_p, '', '', 'BPA', :prd_cmp, 0, 0, 0, 0, 0, 0,0,0);

   delete from s_prd
   where s_prd.prd_org = 'BPI'
     and s_prd.prd_pa = :prd_pa;

  suspend;
  end

end^

SET TERM ; ^