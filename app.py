from flask import Flask, render_template, url_for, redirect, session, request, flash, abort, send_from_directory, make_response
import json
from helper import htmx_request, resolve_redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import SECRET_KEY, DB_URL, UPLOAD_FOLDER, Files
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import RequestEntityTooLarge, UnsupportedMediaType
from forms import LoginForm, RegisterForm, ResetPasswordForm, UpdateEmailForm, ProfilePhotoForm, UpdateUsernameForm
from models import *
from datetime import timedelta
from sub.Gameplay import Gameplay, ComputerPlayer, DataHandler, ScoreTracker
from codes import CODES
from time import sleep
from urllib.parse import urlparse, parse_qs
from pathlib import Path

def create_app():
    # APP CONFIG
    app = Flask(__name__, static_folder='./static')
    app.secret_key = SECRET_KEY

    app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
    app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(hours=12)

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1000 * 1000 #100mb 
    app.config['UPLOAD_EXTENSIONS'] = Files.IMAGE_EXTS

    # CREATE INSTANCE OF FLASK_SQL_ALCHEMY and MARSHMALLOW
    db.init_app(app)

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = '/login'
    login_manager.login_message = ''

    @login_manager.user_loader
    def user_loader(user_id):
        return User.get_by_id(user_id)

    # TODO: Logging
    # prevent caching pages on logout
    @app.after_request
    def after_request(response):   
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    # TO DO: Function for error handlers
    # ======================= ERROR HANDLERS ==========================
    # set up 404 page
    @app.errorhandler(CODES.NOT_FOUND)
    def ab_not_found(e):
        if 'hx-request' in request.headers:
            return resolve_redirect(url_for('not_found'))
        
        return render_template('pages/codes/err_code.html', code=str(CODES.NOT_FOUND), message="Page Not Found!") 

    @app.route(f'/{CODES.NOT_FOUND}', methods=['GET'])
    def not_found():
        return abort(CODES.NOT_FOUND)

    @app.errorhandler(CODES.NOT_ALLOWED)
    def ab_method_not_allowed(e):
        if 'hx-request' in request.headers:
            return resolve_redirect(url_for('not_allowed'))
        
        return (render_template('pages/codes/err_code.html', 
                                code=str(CODES.NOT_ALLOWED), 
                                message="Method Not Allowed!", sub_message="You should be redirected in a few seconds... if not click here."),
                                {"Refresh": f"2; url={url_for('index')}"}
        )

    # allow htmx to redirect to this 404
    @app.route(f'/{CODES.NOT_ALLOWED}', methods=['GET'])
    def not_allowed():
        return abort(CODES.NOT_ALLOWED)


    # ====================== MIDDLEWARE ==========================
    def parse_next(request):
        ref = urlparse(request.referrer)
        next=parse_qs(ref.query).get('next')
        if next:
            next = next[0]
        else:
            next = ref.path 
            if next and ref.query:
                next += '?' + ref.query
            
        return next

    # ======================= ROUTES ==========================
    @app.route('/uploads/<path:filename>')
    @login_required
    def upload(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)

    # =============== INDEX PAGE ===================== --working
    @app.route('/', methods=['GET'])
    def index():

        # PVELeaderBoard.reset_leaderboard()
        # PVPLeaderBoard.reset_leaderboard()
        
        mode = "1P"
        level = int(session.get('level', 1))
        level_text = ComputerPlayer.LEVELS[level]
        return render_template('pages/index.html', mode=mode, level=level, level_text=level_text)
        

    # ================= REGISTER ===================== --working
    @app.route('/register/guest', methods=['GET'], endpoint='register_guest')
    @app.route('/register', methods=['GET'])
    def register():

        guest = request.endpoint == 'register_guest'

        if current_user.is_authenticated and not guest:
            return redirect(url_for('index'))

        form = RegisterForm()
        resp = make_response(render_template('pages/auth/register.html', form=form, guest=guest))
        resp.headers["HX-Trigger-After-Swap"] = 'initInputs'
        return resp
        
    @app.route('/register', methods=['POST'])
    @htmx_request
    def register_request():
        
        form = RegisterForm()
        guest = request.form.get('guest')

        if not form.validate_on_submit():
            return render_template('htmx/form-errors.html', errors=form.errors)

        email = form.email.data
        username = form.username.data

        query = db.select(User).filter(db.or_(User.email==email, User.username==username))
        existing_user = db.session.scalars(query).first()

        if existing_user:
            return render_template('htmx/notif.html', message='A user with this email already exists', type='error')
        
        user_obj = User()
        
        form.populate_obj(user_obj)
        user_obj.password = generate_password_hash(user_obj.password)

        db.session.add(user_obj)
        db.session.commit()

        pve_lb = PVELeaderBoard(user=user_obj)
        pvp_lb = PVPLeaderBoard(user=user_obj)

        db.session.add(pvp_lb)
        db.session.add(pve_lb)
        db.session.commit()

        if guest == 'guest':
            session['guest'] = user_obj.id
        else:
            login_user(user_obj)
        
        flash(f'Welcome, {user_obj.fname} ', 'success')
        next_url = parse_next(request)
        red_url = next_url if next_url else url_for('index')
        return resolve_redirect(red_url)

    # =====================LOGIN ============================= --working
    @app.route('/login/guest', methods=['GET'], endpoint='login_guest')
    @app.route('/login', methods=['GET'])
    def login():

        guest = request.endpoint == 'login_guest'

        if current_user.is_authenticated and not guest:
            return redirect(url_for('index'))
        
        if not current_user.is_authenticated and guest:
            flash('You must be logged in before signing un your guest.', 'warning')
            return resolve_redirect(url_for('login'))
        
        form = LoginForm()
        resp = make_response(render_template('pages/auth/login.html', form=form, guest=guest))
        resp.headers["HX-Trigger-After-Swap"] = 'initInputs'
        return resp


    @app.route('/login', methods=['POST'])
    def login_request():

        form = LoginForm()
        guest = request.form.get('guest')
        is_guest = guest == 'guest'

        if not current_user.is_authenticated and guest:
            flash('You must be logged in before signing un your guest', 'warning')
            return resolve_redirect(url_for('login'))
        

        if not form.validate_on_submit():
            return render_template('htmx/form-errors.html', errors=form.errors)

        username = form.username.data
        password = form.password.data

        existing_user = User.get_by_uname_or_email(username)
    
        # check if user exists and password is correct
        if not existing_user or not check_password_hash(existing_user.password, password):
            return render_template('htmx/notif.html', message='Unable To Log in... Check your credentials', type='error')
    
        # check if user is guest and 
        elif is_guest:

            # check if the guest who tried to log is the the current user
            if (current_user.is_authenticated and current_user.id == existing_user.id):
                return render_template('htmx/notif.html', message='Guest account cannot log in', type='error')
        
            # set the session guest if user is guest and is not the current user
            session['guest'] = existing_user.id
            session['guest_uname'] = existing_user.username
            
        else:
            login_user(existing_user)

        flash(f"Logged in {'(Guest)' if is_guest else ''} successfully as {existing_user.fname}", 'success')

        next_url = parse_next(request)
        red_url = next_url if next_url else url_for('index')
        return resolve_redirect(red_url)
        
    # ======================= LOGOUT VIA POST ========================== --working
    @app.route('/logout', methods=['POST'])
    @login_required
    def logout():
        logout_user()
        session.clear()
        return resolve_redirect(url_for('index', ref='sign-out'))


    # TODO: implement first or 404s
    # ======================= PROFILE ==========================

    @app.route('/profile/update/username', methods=['GET'], endpoint='update_username')
    @app.route('/profile/update/email', methods=['GET'], endpoint='update_email')
    @app.route('/reset-password', methods=[ "GET"], endpoint="reset_password")
    @app.route("/profile/<string:username>/photo", methods=["GET"], endpoint="profile_photo")
    @app.route('/profile/<string:username>', methods=['GET'])
    # @login_required
    def profile(username=None):

        # allow to view other profile pages
        mode = request.args.get('mode', 'pve')

        # TODO: Convert all to pvp and pve/1p and 2p for consistency
        if mode =='2P':
            mode = 'pvp'
        elif mode == '1P':
            mode = 'pve'

        if mode not in ('pve', 'pvp'):
            abort(404)

        if request.endpoint in ('update_email', 'reset_password', 'update_username', 'profile_photo'):
            user = current_user
        else:
            user = User.get_by_uname_or_email(username)

        if not user:
            abort(404)

        if mode == 'pve':
            rank = user.pve_leaderboard.get_user_rank()
            leaderboard = user.pve_leaderboard
        else:
            rank = user.pvp_leaderboard.get_user_rank()
            leaderboard = user.pvp_leaderboard

        is_user = user == current_user
        photo_context = {
            'active': request.endpoint == 'profile_photo',
            'form': ProfilePhotoForm()
        }

        reset_context = {
            'active': request.endpoint == 'reset_password',
            'form': ResetPasswordForm()
        }

        email_context = {
            'active': request.endpoint == 'update_email',
            'form': UpdateEmailForm(email=user.email)
        }

        username_context = {
            'active': request.endpoint == 'update_username',
            'form': UpdateUsernameForm(username=user.username)
        }
        

        return render_template('pages/account/profile.html', 
                            user=user, 
                            rank=rank, 
                            leaderboard=leaderboard, mode=mode, 
                            photo_context=photo_context, 
                            reset_context=reset_context,
                            email_context=email_context,
                            username_context=username_context,
                            is_user=is_user
                            )

    # profile_updates 
    # email
    @app.route('/profile/update/email', methods=['POST'])
    @login_required
    def update_email_request():
        
        form = UpdateEmailForm()
        if not form.validate_on_submit():
            return render_template('htmx/form-errors.html', errors=form.errors)

        existing_user = User.get_by_uname_or_email(form.email.data)
        if existing_user:
            if existing_user.id == current_user.id:
                return render_template('htmx/notif.html', message='No Changes Made!', type='info')
            
            return render_template('htmx/notif.html', message='A user with this email already exists', type='error')
        
        current_user.email = form.email.data
        db.session.commit()
        flash('Email Updated Successfully', 'success')
        return resolve_redirect(url_for('profile', username=current_user.username))

    # username
    @app.route('/profile/update/username', methods=['POST'])
    @login_required
    def update_username_request():

        form = UpdateUsernameForm()
        if not form.validate_on_submit():
            return render_template('htmx/form-errors.html', errors=form.errors)

        existing_user = User.get_by_uname_or_email(form.username.data)
        if existing_user:
            if existing_user.id == current_user.id:
                return render_template('htmx/notif.html', message='No Changes Made!', type='info')
            return render_template('htmx/notif.html', message='A user with this username already exists', type='error')
        
        current_user.username = form.username.data
        db.session.commit()
        flash('Username Updated Successfully', 'success')
        return resolve_redirect(url_for('profile', username=current_user.username))
        
    @app.route('/profile/update/photo', methods=['POST'])
    @login_required
    def update_profile_pic():


        file = request.files.get('photo')
        if not file:
            current_user.profile_pic = None
            db.session.commit()
            return resolve_redirect(url_for('profile', username=current_user.username))
        
        try:
            form = ProfilePhotoForm()

            if not form.validate_on_submit():
                print('Form Errors', form.errors)        
                return render_template('htmx/notif.html', message='Invalid File Type', type='error'), CODES.UNSUPPORTED_MEDIA_TYPE
            

            output = Path(app.config['UPLOAD_FOLDER']) / current_user.build_path('profile', f'profile.png') 
            output.parent.mkdir(exist_ok=True, parents=True)
            file.save(output)

            current_user.profile_pic = 'profile_set'
            db.session.commit()
            flash('Profile Updated', 'success')
            return resolve_redirect(url_for('profile', username=current_user.username))

        except RequestEntityTooLarge:
            return render_template('htmx/notif.html', message ="File too large (max: 10mb)" , type='error'), CODES.CONTENT_TOO_LARGE
        
        except UnsupportedMediaType:
            return render_template('htmx/notif.html', message ="Invalid File Type" , type='error'), CODES.UNSUPPORTED_MEDIA_TYPE
        
        except Exception as e:
            print(e)
            return render_template('htmx/notif.html', message ="Unable to upload file" , type='error'), CODES.BAD_REQUEST

    # RESET PASSWORD
    @app.route('/reset-password', methods=[ "POST"])
    @login_required
    def reset_password_request(): 
            
        form = ResetPasswordForm()
        if not form.validate_on_submit():
            return render_template('htmx/form-errors.html', errors=form.errors)
            
        if not check_password_hash(current_user.password, form.old_password.data):
            return render_template('htmx/notif.html', message='Old Password is incorrect', type='error')
        
        if check_password_hash(current_user.password, form.password.data):
            return render_template('htmx/notif.html', message='Old Password cannot be the same as new password', type='error')
            
        current_user.password = generate_password_hash(form.password.data)
        db.session.commit()

        flash('Password Updataed Succesfully', 'success')
        return resolve_redirect(url_for('profile', username=current_user.username))

        
    # ======================= GAMEPLAY ==========================
    @app.route('/play', methods=['POST'], endpoint='play_setup')
    def play_setup():

        """Sets up the game and redirects to the gameplay page (post, redirect, get pattern)"""
        # defautl to single player
        mode = request.form.get('mode', "1P")
        return resolve_redirect(url_for('play', mode=mode))

    @app.route('/play/<string:mode>', methods=['GET'])
    @login_required
    def play(mode="1P"):
        """Sets up the game and redirects to the gameplay page"""

        if mode not in ("1P", "2P"):
            return abort(404)
        
        # set up default values for flask template context
        guest_obj = None
        level_text = None
        user_leaderboard = current_user.pve_leaderboard if mode == "1P" else current_user.pvp_leaderboard
        user_rank = user_leaderboard.get_user_rank()
        guest_rank = None

        if mode == '1P':
            # game = session.get('game_pve')
            # if not game:
            # -1 is the computer player id
            score_tracker = ScoreTracker(current_user.id, -1)
            game = Gameplay(current_user.id, -1, score_tracker)
            session['game_pve'] = DataHandler.serialize(game)
            # else:
                # game = DataHandler.deserialize(game)
            level = int(session.get('level', 1))
            level_text = ComputerPlayer.LEVELS[level]
            # comp turn on load
            # if game.turn != current_user.id:
            #     print("executing comp turn on load")
            #     return move()

        elif mode == "2P":
            guest = session.get("guest")
            if not guest:
                return redirect(url_for('login_guest', next=url_for('play', mode="2P")))
            
            # game = session.get('game_pvp')
            # if not game:
            score_tracker = ScoreTracker(current_user.id, guest)
            game = Gameplay(current_user.id, guest, score_tracker)
            session['game_pvp'] = DataHandler.serialize(game)

            guest_obj = User.get_by_id(session.get("guest"))
            guest_rank = guest_obj.pvp_leaderboard.get_user_rank()
        

        return render_template('pages/gameplay/play.html', mode=mode, user_rank=user_rank, guestObj=guest_obj, guest_rank=guest_rank, level_text=level_text)
        
    @app.route('/move', methods=['POST'])
    @login_required
    def move():
        """Handles the user move and computer move"""

        move = request.form.get('move')
        mode = request.form.get('mode')
        
        if not mode or mode not in ("1P", "2P"):
            # check if no mode set
            flash("Please select a game mode", "warning")
            return resolve_redirect(url_for('index'))
        
        session_mode = "game_pvp" if mode == "2P" else "game_pve"
        # retrieve the session game
        game = DataHandler.deserialize(session[session_mode])

        # context variablies
        ended = None
        text = None 
        comp_turn = (game.turn != current_user.id and mode == "1P")
        initial_turn = game.turn
        cp_context = None
        scores_context = None
        loser = None
        headers = {}
        points = ''
        
        # check if the game is still ongoing
        if game.gamestate == game.PLAYING:

            # check if the user is trying to play out of turn
            if comp_turn and move:
                return {}, CODES.NO_CONTENT

            # check if the user move is valid
            elif move and game.valid_move(move):
                # get the user text to display in the bpx and play the move
                # if not comp_turn:
                text = game.get_text()
                ended = game.player_move(move)
            
            elif comp_turn and not ended:
                level = int(session.get('level', 1))
                cp = ComputerPlayer(opponent=current_user.id, difficulty=level)
                cp_move = cp.get_move(game)
                cp_text = game.get_text()

                # simulate computer thinking before playing to ensure game turn and move are in sync and animate pointer
                sleep(1)
                ended = game.player_move(cp_move)
                cp_context = {'move':cp_move, 'text': cp_text}

            # TODO: Clean this up
            if ended:
                leaderboard_type = 'pve' if mode == "1P" else 'pvp'

                if ended != game.DRAW:
                    loser = game.x_player if game.turn == game.o_player else game.o_player
                    if loser != -1:
                        points = User.get_by_id(loser).set_points('l', leaderboard_type)
                    
                    if game.turn != -1:
                        points = User.get_by_id(game.turn).set_points('w',  leaderboard_type)

                    headers = {
                                'HX-Trigger-After-Swap': {'drawLine': 
                                {
                                'orientation': ended[0], 
                                'start': ended[1][0],
                                'end': ended[1][1]
                                }
                            },
                        }
                    # TODO: show correct points on win, unit testing
                else:
                    if game.x_player != -1:
                        points = User.get_by_id(game.x_player).set_points('d', leaderboard_type)
                    
                    if game.o_player != -1:
                        points = User.get_by_id(game.o_player).set_points('d', leaderboard_type)
                
            remaining_cells = game.available_moves()
            session[session_mode] = DataHandler.serialize(game)
            if ended:
                scores_context = game.score_tracker.get_scores()
                scores_context['points'] = points
                block = {'blockButtons' : {'cls':'forfeit', 'blocked':True}}
                if 'HX-Trigger-After-Swap' in headers:
                    headers['HX-Trigger-After-Swap'] |= block
                else:
                    headers['HX-Trigger-After-Swap'] = block

            elif mode == "1P" and text:
                headers = {
                                'HX-Trigger-After-Swap': 'compPlay' 
                                
                        }
                
            # NOTE: A string returned from a view is automatically wrapped in a response by Flask, so if I want to include headers
            # I need to create a response obj for myself
            # https://stackoverflow.com/questions/29464276/add-response-headers-to-flask-web-app
            # Attempting to trigger winne draw aimation from server side

            response = make_response(render_template('htmx/gameplay/move.html', 
                                mode=mode, 
                                ended=ended, 
                                remaining_cells=remaining_cells, text=text, 
                                as_user=initial_turn == current_user.id, 
                                winner=game.turn, 
                                cp_context=cp_context,
                                scores_context=scores_context,
                                loser=loser
                                ))

            if headers:
                after_swap = headers.get('HX-Trigger-After-Swap')
                if type(after_swap) == dict:
                    response.headers.set("HX-Trigger-After-Swap", json.dumps(after_swap))
                else:
                    response.headers.set("HX-Trigger-After-Swap",after_swap)

            return response

        
        return {}, CODES.NO_CONTENT

    @app.route('/level', methods=['POST'], endpoint="select_level")
    @app.route('/mode', methods=['POST'], endpoint="select_mode")
    @htmx_request
    @login_required
    def select():
        """Selects/swaps the game mode either 1P or 2P"""
        mode = request.form.get('mode')
        level = request.form.get('level')
        level_context = None

        if request.endpoint == "select_mode":
            mode = "2P" if mode == "1P" else "1P"
            if mode == "1P":
                level = session.get('level', 1)
                level_text = ComputerPlayer.LEVELS[level]
                level_context = {
                    'level': level,
                    'text': level_text
                }

        elif request.endpoint  == "select_level" and level and mode == "1P":
            level = int(level) + 1

            if level > 3:
                level %= 3

            level_text = ComputerPlayer.LEVELS[level]
            session['level'] = level
            level_context = {
                    'level': level,
                    'text': level_text,
                    "level_only": True
                }
            mode = None

        return render_template('htmx/gameplay/select.html', mode=mode, level_context=level_context)

    @app.route('/reset', methods=['GET'])
    def reset():

        mode = request.args.get('mode')
        session_mode = "game_pvp" if mode == "2P" else "game_pve"

        game = session.get(session_mode)

        gameObj = DataHandler.deserialize(game)

        # swap players as x and o when resetting the board and make sure to keep the same score tracker
        new_game = Gameplay(gameObj.o_player, gameObj.x_player, gameObj.score_tracker)
        comp_turn = new_game.turn != current_user.id
        session[session_mode] = DataHandler.serialize(new_game)
        
        response = make_response(render_template('htmx/gameplay/reset.html', mode=mode, comp_turn=comp_turn) )
        response.headers.set("HX-Trigger-After-Swap", json.dumps({'blockButtons' : {'cls':'forfeit', 'blocked':False}}))
        return response

    @app.route('/forfeit', methods=['POST'])
    @htmx_request
    @login_required
    def forfeit():
        """Forfeits the current game and redirects to the index page"""
        # TODO: Player indidcatort and forfeit confirmation --done
        mode = request.form.get('mode')
        ffer = request.form.get('forfeit')
        if (not mode or mode not in ("1P", "2P")) or ffer not in ("home", "away"):
            return abort(404)
        
        session_mode = "game_pvp" if mode == "2P" else "game_pve"

        game = DataHandler.deserialize(session[session_mode])

        if game.gamestate != game.PLAYING:
            return  {}, CODES.NO_CONTENT
        
        game.score_tracker.forfeit(ffer)
        scores_context = game.score_tracker.get_scores()
        session[session_mode] = DataHandler.serialize(game)

        # update the leader board with forfeith points
        if mode == "2P":
            if ffer == "home": 
                current_user.set_points('l', 'pvp')
                User.get_by_id(game.score_tracker.away).set_points('w', 'pvp')

            else:
                current_user.set_points('w', 'pvp')
                User.get_by_id(game.score_tracker.away).set_points('l', 'pvp')

        else:
            current_user.set_points('w', 'pve')
            
        return render_template('htmx/gameplay/reset.html', forfeit=True, scores_context=scores_context, user_turn=game.turn == current_user.id)

    @app.route('/remove-guest', methods=['POST'])
    @login_required
    def remove_guest():
        """ removes the currently logged in guest if any"""
        session.pop('guest', None)
        return resolve_redirect(url_for('index'))

    @app.route('/leaderboard', methods=['GET'])
    @login_required
    def leaderboard():
        
        mode = request.args.get('mode', 'pve')

        if mode not in ('pve', 'pvp'):
            abort(404)
        
        if mode == 'pve':
            leaderboard = PVELeaderBoard().get_dense_rank()
        else:
            leaderboard = PVPLeaderBoard().get_dense_rank()

        return render_template('pages/gameplay/leaderboard.html', leaderboard=leaderboard, mode=mode)

    # ======================= HTMX_SPECS ========================== --working
        
    @app.route('/close-modal', methods=['GET'])
    @htmx_request
    # @login_required
    def close_modal():
        return render_template('htmx/modals/closed-modal.html')

    @app.route('/dev-not-imp', methods=['GET','POST'])
    @htmx_request
    def not_implemented():
        return render_template('htmx/notif.html', message ="Not implemented yet" , type='info')

    @app.route('/clear', methods=['GET'])
    @htmx_request
    def clear():
        return ' '
    
    return app

    # if __name__ == '__main__':
    #     app.run(debug=True, port=7000)

    #     with app.app_context():
    #         db.session.close()