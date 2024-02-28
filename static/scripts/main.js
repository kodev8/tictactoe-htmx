function controlInputLength (e, maxlength) {
    let length = e.target.value.length
    if (length >= maxlength){
        e.target.value = e.target.value.slice(0, maxlength)

    }  
    formatted_length = e.target.value.length
    document.getElementById('count').innerHTML = formatted_length
}

//  links a given elleemtn to the item it shows on hover
function linkhHoverShow(element, to_hover) {
    element?.addEventListener('mouseenter', ()=>  {
        ht = setTimeout(()=>{
            to_hover?.classList.remove('invisible')
            element.over.focus()
    }, 500)

    } )

    element?.addEventListener('mouseleave', ()=> {

        if(!to_hover.matches(':hover')){
        clearTimeout(ht)
        to_hover?.classList.add('invisible')}
    })

    to_hover?.addEventListener('mouseleave', ()=> {

        if(!element.matches(':hover')){
        clearTimeout(ht)
        to_hover?.classList.add('invisible')}
    })

    let isMobile = false;

    element?.addEventListener('touchstart', () => {
        isMobile = true;
    });

    element?.addEventListener('click', (event) => {
        if (isMobile) {
            event.preventDefault()
            // Handle the click action for mobile devices
            if (to_hover.classList.contains('invisible')) {
                to_hover.classList.remove('invisible');
            } else {
                to_hover.classList.add('invisible');
            }
            isMobile = false; // Reset the flag
        }
    });
    
}

function handleCustomInputs() {
    document.querySelectorAll('.custom-input-group')?.forEach(customInputGroup => {
        let customInput = customInputGroup.querySelector('.custom-input')
        customInput.addEventListener('input', (event) => {
            let inlineError = customInputGroup.querySelector('.inline-error')
            inlineError.innerHTML = ''
        })
      
        // let eye ico control if text input is password or text
        let eyeIcon = customInput.parentNode.querySelector('.eye-icon')
        if(eyeIcon){
          eyeIcon.addEventListener('click', (e)=> {
      
            e.preventDefault();
              if(customInput.type == 'password') {
                  eyeIcon.classList.remove('fa-eye-slash')
                  eyeIcon.classList.add('fa-eye')
                  customInput.type='text'
              }else {
                eyeIcon.classList.remove('fa-eye')
                eyeIcon.classList.add('fa-eye-slash')
                customInput.type='password'
      
              }
            })
          }
        })
}
function closeNotif(element) {
    element.closest('.notif')?.classList.remove('noti-open')
    element.closest('.notif')?.classList.add('noti-close')
}

function toggleDropdown(ele) {
    let dropdown = ele.querySelector('#user-dropdown')
    
    dropdown.classList.toggle('invisible')
    ele.addEventListener('mouseleave', ()=>dropdown.classList.add('invisible'))
    dropdown.addEventListener('mouseleave', ()=>dropdown.classList.add('invisible'))
}

function dth (event, target) {
    

    let t = target instanceof HTMLElement ? target : event.target.querySelector(target)
    t.classList.toggle('invisible')

    document.addEventListener("click", (e) => {
    if (!event.target.contains(e.target)) {
        t.classList.add("invisible");
    }
    });
}


function toggleAll (element, ...classes) {
    classes.forEach(c => element.classList.toggle(c))
}


// function closeSideNav() {

//     let sideNav = document.querySelector('#tw-side-nav')
//     sideNav.classList.remove('translate-x-0')
//     sideNav.classList.add('translate-x-[100%]')
//     let modal = document.querySelector('#modal-bg')
//     modal.classList.add('hidden')
// }

// window.addEventListener('resize', ()=> {
//     if(window.innerWidth > 640) {
//         closeSideNav()
//     }
// })

// function openSideNav() {
//     //   console.log('hy')
//     let sideNav = document.querySelector('#tw-side-nav')
//     sideNav.classList.remove('translate-x-[100%]')
//     sideNav.classList.add('translate-x-0')

//     let modal = document.querySelector('#modal-bg')
//     modal.classList.remove('hidden')
//     modal.onclick = closeSideNav
// }

function drawLine(orientation, start, stop) {
    let board = document.querySelector('#board')
    let svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    let line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    
    svg.classList.add('absolute', 'h-full', 'w-full', 'pointer-events-none')
    svg.setAttribute('id', 'winner-line')

    line.classList.add('stroke-[#e3cf1a7c]', 'stroke-2')

    start = parseInt(start)
    stop = parseInt(stop)


    // increment starts and sops to account for horizontal lines in board
    if (start > 2) {
        start ++
    }
    if (stop > 2) {
        stop ++
    }

    if (start > 6) {
        start ++
    }

    if (stop > 6) {
        stop ++
    }

    let children = board.children 
    let initial = children.item(start)
    let end = children.item(stop)

    let icenterX, icenterY, ecenterX, ecenterY;

    if (orientation == 'v') {
        // take centered x and boost y to top of initial and bottom of end
        icenterX = initial.offsetLeft + initial.offsetWidth / 2;
        icenterY = initial.offsetTop;

        ecenterX = end.offsetLeft + end.offsetWidth / 2;
        ecenterY = end.offsetTop + end.offsetHeight;

    }else if (orientation == 'h') {
        // take centered y and boost x to left of initial and right of end
        icenterX = initial.offsetLeft;
        icenterY = initial.offsetTop + initial.offsetHeight / 2;

        ecenterX = end.offsetLeft + end.offsetWidth;
        ecenterY = end.offsetTop + end.offsetHeight / 2;
        
    }else if (orientation == 'd1'){
        // tl to br - take top left of initial and bottom right of end
        icenterX = initial.offsetLeft;
        icenterY = initial.offsetTop;

        ecenterX = end.offsetLeft + end.offsetWidth;
        ecenterY = end.offsetTop + end.offsetHeight;
        
    }
    else if (orientation == 'd2'){
        // tr to bl - take top right of initial and bottom left of end
        icenterX = initial.offsetLeft + initial.offsetWidth;
        icenterY = initial.offsetTop;

        ecenterX = end.offsetLeft;
        ecenterY = end.offsetTop + end.offsetHeight;
    }

    line.setAttribute('x1', icenterX)
    line.setAttribute('y1', icenterY)

    // Create and set up the animation elements
    let animateX = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateX.setAttribute('attributeName', 'x2');
    animateX.setAttribute('attributeType', 'XML');
    animateX.setAttribute('from', icenterX);
    animateX.setAttribute('to', ecenterX);
    animateX.setAttribute('dur', '0.7s');
    animateX.setAttribute('fill', 'freeze');

    let animateY = document.createElementNS('http://www.w3.org/2000/svg', 'animate');
    animateY.setAttribute('attributeName', 'y2');
    animateY.setAttribute('attributeType', 'XML');
    animateY.setAttribute('from', icenterY);
    animateY.setAttribute('to', ecenterY);
    animateY.setAttribute('dur', '0.7s');
    animateY.setAttribute('fill', 'freeze');

    // Append the animations to the line element
    line.appendChild(animateX);
    line.appendChild(animateY);

    svg.appendChild(line);

    line.setAttribute('x2', ecenterX);
    line.setAttribute('y2', ecenterY);

    board.appendChild(svg)
}


function blockButtons(cls, blocked) {
    console.log('block')
    let bs = document.querySelectorAll(`.${cls}`)
    bs?.forEach(b => {

        if (blocked) {
            b.classList.add('disabled')
            b.disabled = true
        }
        else {
            b.classList.remove('disabled')
            b.disabled = false
        }
        }
    )
}

function toggleStats(element) {
    element.parentElement.querySelectorAll('.stat-container').forEach(con => {
        if (con === element.nextElementSibling || con.classList.contains('max-h-[1200px]')) {
            toggleAll(con, 'max-h-0', 'max-h-[1200px]', 'sm:max-w-0', 'max-w-[1200px]');
            toggleAll(con.previousElementSibling, "rotate-180", "sm:rotate-[-90deg]", "sm:rotate-90")

        }
        

    });
}