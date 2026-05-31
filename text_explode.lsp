(vl-load-com)

;; combined WCS bounding box of every object in a selection set
(defun ss-bbox ( ss / i obj mn mx allMin allMax )
  (setq i 0)
  (while (< i (sslength ss))
    (setq obj (vlax-ename->vla-object (ssname ss i)))
    (vla-getboundingbox obj 'mn 'mx)
    (setq mn (vlax-safearray->list mn)
          mx (vlax-safearray->list mx))
    (if allMin
      (setq allMin (mapcar 'min allMin mn)
            allMax (mapcar 'max allMax mx))
      (setq allMin mn  allMax mx))
    (setq i (1+ i)))
  (list allMin allMax))

(defun c:TXT2GEO ( / ss tmp box origMin origMax origW
                     blk nb nMin nMax nW sf oce ofd )
  (princ "\nSelect text / mtext to convert to geometry: ")
  (setq ss (ssget '((0 . "TEXT,MTEXT"))))
  (cond
    ((null ss) (princ "\nNothing selected.") (princ))
    (t
      (setq oce (getvar "CMDECHO")
            ofd (getvar "FILEDIA"))
      (setvar "CMDECHO" 0)
      (setvar "FILEDIA" 0)

      ;; 1. record original size + location
      (setq box     (ss-bbox ss)
            origMin (car box)
            origMax (cadr box)
            origW   (- (car origMax) (car origMin)))

      ;; 2. export selection to a temp WMF
      (setq tmp (vl-filename-mktemp "txt2geo" nil ".wmf"))
      (command "_.WMFOUT" tmp ss "")

      ;; 3. reimport it (insertion 0,0, accept default scale/rotation)
      (command "_.WMFIN" tmp "0,0" "" "" "")
      (setq blk (entlast))

      ;; 4. measure the imported block and scale it to the original width
      (vla-getboundingbox (vlax-ename->vla-object blk) 'nMin 'nMax)
      (setq nMin (vlax-safearray->list nMin)
            nMax (vlax-safearray->list nMax)
            nW   (- (car nMax) (car nMin)))
      (if (> nW 1e-8)
        (progn
          (setq sf (/ origW nW))
          (command "_.SCALE" blk "" (list (car nMin) (cadr nMin)) sf)))

      ;; 5. move it back onto the original location
      (vla-getboundingbox (vlax-ename->vla-object blk) 'nMin 'nMax)
      (setq nMin (vlax-safearray->list nMin))
      (command "_.MOVE" blk "" nMin origMin)

      ;; 6. explode into editable geometry, clean up
      (command "_.EXPLODE" blk)
      (command "_.ERASE" ss "")
      (vl-file-delete tmp)

      (setvar "CMDECHO" oce)
      (setvar "FILEDIA" ofd)
      (princ "\nDone. Run OVERKILL / PEDIT to tidy the geometry.")
      (princ))))