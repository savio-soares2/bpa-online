SET TERM ^ ;

CREATE OR ALTER PROCEDURE CORRIGE_SEQUENCIA_BPA 
returns (
    prd_uid varchar(7),
    prd_pa varchar(10),
    prd_cbo varchar(6),
    prd_flh varchar(3),
    prd_seq varchar(2),
    prd_idade varchar(3),
    prd_qt_p double precision,
    prd_org varchar(3),
    prd_flh_novo varchar(3),
    prd_seq_novo varchar(2))
as
declare variable fol_novo integer;
declare variable seq_novo integer;
declare variable cnes varchar(7);
begin
  fol_novo = 0;
  seq_novo = 0;
  cnes = '';
  for select s_prd.prd_uid,
             s_prd.prd_pa,
             s_prd.prd_cbo,
             s_prd.prd_flh,
             s_prd.prd_seq,
             s_prd.prd_idade,
             s_prd.prd_qt_p,
             s_prd.prd_org
      from s_prd
      where s_prd.prd_org = 'BPA'
      --  and s_prd.prd_uid = '2467879'
      order by 1
      into :prd_uid, :prd_pa, :prd_cbo, :prd_flh, :prd_seq, :prd_idade, :prd_qt_p, :prd_org
   do begin

      seq_novo = :seq_novo + 1;
      if (:prd_uid <> :cnes) then
      begin
        cnes = :prd_uid;
        seq_novo = 1;
        fol_novo = 1;

      end

    if (:seq_novo > 20) then
    begin
     seq_novo = 1;
     fol_novo = :fol_novo + 1;

    end

    prd_flh_novo = SM_PADLEFT(cast(:fol_novo as varchar(3)),0,3);
    prd_seq_novo = SM_PADLEFT(cast(:seq_novo as varchar(2)),0,2);

    update s_prd set s_prd.prd_flh = :prd_flh_novo, s_prd.prd_seq = :prd_seq_novo
    where s_prd.prd_uid = :prd_uid
      and s_prd.prd_pa = :prd_pa
      and s_prd.prd_cbo = :prd_cbo
      and s_prd.prd_flh = :prd_flh
      and s_prd.prd_seq = :prd_seq
      and s_prd.prd_idade = :prd_idade
      and s_prd.prd_qt_p = :prd_qt_p
      and s_prd.prd_org = :prd_org;

    


    suspend;
   end
end^

SET TERM ; ^