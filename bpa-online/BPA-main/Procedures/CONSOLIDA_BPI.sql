SET TERM ^ ;

CREATE OR ALTER PROCEDURE CONSOLIDA_BPI 
as
declare variable v_cnsmed varchar(15);
declare variable v_cnspac varchar(15);
declare variable v_pa varchar(10);
declare variable v_cmp varchar(6);
declare variable v_keep integer;
declare variable v_sum double precision;
BEGIN
 FOR
 SELECT PRD_CNSMED, PRD_CNSPAC, PRD_PA, PRD_CMP -- Coluna CMP adicionada
FROM S_PRD
WHERE PRD_ORG = 'BPI'
GROUP BY PRD_CNSMED, PRD_CNSPAC, PRD_PA, PRD_CMP
HAVING COUNT(*) > 1
 INTO :v_cnsmed, :v_cnspac, :v_pa, :v_cmp
 DO
 BEGIN
 SELECT MIN(PRD_ID), SUM(PRD_QT_P)
 FROM S_PRD
WHERE PRD_ORG = 'BPI'
AND PRD_CNSMED = :v_cnsmed
AND PRD_CNSPAC = :v_cnspac
AND PRD_PA = :v_pa
AND PRD_CMP = :v_cmp
 INTO :v_keep, :v_sum;

 UPDATE S_PRD
 SET PRD_QT_P = :v_sum
 WHERE PRD_ID = :v_keep;

 DELETE FROM S_PRD
 WHERE PRD_ORG = 'BPI'
 AND PRD_CNSMED = :v_cnsmed
 AND PRD_CNSPAC = :v_cnspac
 AND PRD_PA = :v_pa
 AND PRD_CMP = :v_cmp
 AND PRD_ID <> :v_keep;
 END
END^

SET TERM ; ^